"""
SCAPE-ZK — Merkle integrity benchmark.

Measures:
  - leaf_hash:        h_i = H(CT_EHR_i || meta_i)
  - merkle_build:     root construction from leaf hashes
  - merkle_verify:    inclusion-proof verification against the root

This fills the missing primitive timings behind T_hash and T_merk in the
Table IV computation-cost formulas.

Output:
  results/merkle_bench.csv
"""

from __future__ import annotations

import csv
import hashlib
import secrets
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_OUT = ROOT / "results" / "merkle_bench.csv"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

RUNS = 50
WARMUP = 5
N_LEAVES = 16


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash_leaf(ciphertext: bytes, meta: bytes) -> bytes:
    return sha256(ciphertext + meta)


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


def time_op(fn, runs=RUNS, warmup=WARMUP):
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


def main() -> None:
    ciphertexts = [secrets.token_bytes(1024) for _ in range(N_LEAVES)]
    metas = [secrets.token_bytes(96) for _ in range(N_LEAVES)]
    leaf_hashes = [hash_leaf(c, m) for c, m in zip(ciphertexts, metas)]
    levels = build_tree(leaf_hashes)
    root = levels[-1][0]
    proof = build_proof(levels, 3)
    assert verify_proof(leaf_hashes[3], proof, root), "Merkle proof sanity check failed"

    leaf_stats = time_op(lambda: hash_leaf(ciphertexts[0], metas[0]))
    build_stats = time_op(lambda: build_tree(leaf_hashes))
    verify_stats = time_op(lambda: verify_proof(leaf_hashes[3], proof, root))

    ts = datetime.now(timezone.utc).isoformat()
    rows = []
    for op_name, s in [
        ("leaf_hash", leaf_stats),
        ("merkle_build", build_stats),
        ("merkle_verify", verify_stats),
    ]:
        rows.append({
            "timestamp": ts,
            "n_leaves": N_LEAVES,
            "operation": op_name,
            "n_runs": s["n"],
            "mean_ms": round(s["mean"], 6),
            "std_ms": round(s["std"], 6),
            "median_ms": round(s["median"], 6),
            "min_ms": round(s["min"], 6),
            "max_ms": round(s["max"], 6),
        })

    is_new = not CSV_OUT.exists()
    with open(CSV_OUT, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp", "n_leaves", "operation", "n_runs",
                "mean_ms", "std_ms", "median_ms", "min_ms", "max_ms",
            ],
        )
        if is_new:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Saved {CSV_OUT}")


if __name__ == "__main__":
    main()
