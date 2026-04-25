"""
Integrity verification benchmark by EHR file size.

Measures three paper-specific paths:
  1. XAuth-style inquiry integrity:
       T_xauth(size) = T_hash(payload) + T_compare
     Based on the XAuth data-inquiry step: hash stored data and compare it
     to the blockchain-anchored hash value.

  2. SSL-XIoMT-style integrity verification:
       T_ssl(size) = T_hash(payload) + T_commit_hash + T_merkle_verify
     Based on VERIFYCROSSDOMAINAUTHOR / VERIFVZKP style checks where an
     IPFS-linked hash/commitment is validated against a Merkle root.

  3. SCAPE-ZK compact-leaf commitment:
       T_scape(size) = T_hash(compact_meta) + T_merkle_verify

Output:
  results/integrity_filesize_bench.csv
"""

from __future__ import annotations

import csv
import hashlib
import secrets
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.home() / "scape-zk"
CSV_OUT = ROOT / "results" / "integrity_filesize_bench.csv"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

FILE_SIZES_MB = [1, 5, 10, 20, 50, 100]
RUNS = 12
WARMUP = 3
N_LEAVES = 16


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash_internal(left: bytes, right: bytes) -> bytes:
    return sha256(left + right)


def build_tree(leaf_hashes: list[bytes]) -> list[list[bytes]]:
    levels = [leaf_hashes]
    current = leaf_hashes
    while len(current) > 1:
        nxt = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            nxt.append(hash_internal(left, right))
        levels.append(nxt)
        current = nxt
    return levels


def build_proof(levels: list[list[bytes]], index: int) -> list[tuple[bytes, bool]]:
    proof = []
    idx = index
    for level in levels[:-1]:
        sib = idx ^ 1
        if sib >= len(level):
            sibling = level[idx]
        else:
            sibling = level[sib]
        proof.append((sibling, sib > idx))
        idx //= 2
    return proof


def verify_proof(leaf: bytes, proof: list[tuple[bytes, bool]], root: bytes) -> bool:
    cur = leaf
    for sibling, sibling_on_right in proof:
        cur = hash_internal(cur, sibling) if sibling_on_right else hash_internal(sibling, cur)
    return cur == root


def time_op(fn, runs: int = RUNS, warmup: int = WARMUP) -> dict[str, float]:
    times = []
    for i in range(runs + warmup):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        if i >= warmup:
            times.append((t1 - t0) * 1000.0)
    ordered = sorted(times)
    return {
        "n": len(times),
        "mean": statistics.mean(times),
        "std": statistics.stdev(times) if len(times) > 1 else 0.0,
        "median": ordered[len(ordered) // 2],
        "min": ordered[0],
        "max": ordered[-1],
    }


def append_rows(rows: list[dict[str, object]]) -> None:
    is_new = not CSV_OUT.exists()
    with CSV_OUT.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "timestamp",
                "scheme",
                "file_size_mb",
                "operation",
                "n_leaves",
                "n_runs",
                "mean_ms",
                "std_ms",
                "median_ms",
                "min_ms",
                "max_ms",
            ],
        )
        if is_new:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    all_rows: list[dict[str, object]] = []
    ts = datetime.now(timezone.utc).isoformat()

    compact_meta = b"CID||tag||psi||DID"

    for size_mb in FILE_SIZES_MB:
        payload = secrets.token_bytes(size_mb * 1024 * 1024)
        payload_meta = secrets.token_bytes(96)

        payload_hash = sha256(payload + payload_meta)

        # Build a fixed Merkle proof for the SSL-XIoMT-style path.
        ssl_commitment = sha256(payload_hash + compact_meta)
        ssl_other_leaves = [sha256(secrets.token_bytes(128)) for _ in range(N_LEAVES - 1)]
        ssl_leaf_hashes = [ssl_commitment, *ssl_other_leaves]
        ssl_levels = build_tree(ssl_leaf_hashes)
        ssl_root = ssl_levels[-1][0]
        ssl_proof = build_proof(ssl_levels, 0)
        assert verify_proof(ssl_commitment, ssl_proof, ssl_root)

        # Build a fixed Merkle proof for the SCAPE-ZK compact-leaf path.
        compact_leaf = sha256(compact_meta)
        compact_other_leaves = [sha256(secrets.token_bytes(128)) for _ in range(N_LEAVES - 1)]
        compact_leaf_hashes = [compact_leaf, *compact_other_leaves]
        compact_levels = build_tree(compact_leaf_hashes)
        compact_root = compact_levels[-1][0]
        compact_proof = build_proof(compact_levels, 0)
        assert verify_proof(compact_leaf, compact_proof, compact_root)

        payload_hash_stats = time_op(lambda: sha256(payload + payload_meta))
        xauth_compare_stats = time_op(lambda: sha256(payload + payload_meta) == payload_hash)
        ssl_commit_hash_stats = time_op(lambda: sha256(sha256(payload + payload_meta) + compact_meta))
        compact_hash_stats = time_op(lambda: sha256(compact_meta))
        ssl_verify_stats = time_op(lambda: verify_proof(ssl_commitment, ssl_proof, ssl_root))
        compact_verify_stats = time_op(lambda: verify_proof(compact_leaf, compact_proof, compact_root))
        xauth_total_stats = time_op(
            lambda: sha256(payload + payload_meta) == payload_hash
        )
        ssl_total_stats = time_op(
            lambda: verify_proof(sha256(sha256(payload + payload_meta) + compact_meta), ssl_proof, ssl_root)
        )
        scape_total_stats = time_op(
            lambda: verify_proof(sha256(compact_meta), compact_proof, compact_root)
        )

        for scheme, op_name, stats in [
            ("xauth", "payload_hash", payload_hash_stats),
            ("ssl_xiomt", "payload_hash", payload_hash_stats),
            ("xauth", "compare_hash", xauth_compare_stats),
            ("ssl_xiomt", "commit_hash", ssl_commit_hash_stats),
            ("scape_zk", "compact_leaf_hash", compact_hash_stats),
            ("ssl_xiomt", "merkle_verify", ssl_verify_stats),
            ("scape_zk", "merkle_verify", compact_verify_stats),
            ("xauth", "total", xauth_total_stats),
            ("ssl_xiomt", "total", ssl_total_stats),
            ("scape_zk", "total", scape_total_stats),
        ]:
            all_rows.append({
                "timestamp": ts,
                "scheme": scheme,
                "file_size_mb": size_mb,
                "operation": op_name,
                "n_leaves": N_LEAVES,
                "n_runs": stats["n"],
                "mean_ms": round(stats["mean"], 6),
                "std_ms": round(stats["std"], 6),
                "median_ms": round(stats["median"], 6),
                "min_ms": round(stats["min"], 6),
                "max_ms": round(stats["max"], 6),
            })

        print(f"[done] {size_mb} MB")

    append_rows(all_rows)
    print(f"Saved {CSV_OUT}")


if __name__ == "__main__":
    main()
