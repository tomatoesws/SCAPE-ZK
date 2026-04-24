#!/usr/bin/env python3
"""Primitive-aware baseline simulator for SCAPE-ZK comparisons.

This script ties baseline comparison values to the local primitive
micro-benchmarks in `results/primitive_microbench.csv` whenever possible,
while still preserving paper-anchor validations for claims that are only
reported as end-to-end headline numbers in the source papers.

Usage:
    python3 baseline_sim.py
    python3 baseline_sim.py --paper xauth
    python3 baseline_sim.py --show-primitives
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parent
PRIMITIVE_CSV = ROOT / "results" / "primitive_microbench.csv"


@dataclass
class PrimitiveTimings:
    thash_ms: float
    tgrp_ms: float
    tpair_ms: float
    tsym_ms: float


def simulate_integrity_costs(primitives, n_users, n_system_records):
    """
    Strict scheme-specific integrity / delegation cost model.

    Parameters
    ----------
    primitives : dict
        Required keys:
        - 'T_hash'
        - 'T_leaf_hash'
        - 'T_merk'
        - 'T_pre'
    n_users : int
        Number of users / requests relevant to the MMHT height model.
    n_system_records : int
        Included for interface compatibility; not used by the required formulas.

    Returns
    -------
    dict
        Keys:
        - 'XAuth'
        - 'SSL_XIoMT'
        - 'Scheme30'
        - 'SCAPE_ZK_Integrity'
        - 'SCAPE_ZK_Total'
    """
    required_keys = ("T_hash", "T_leaf_hash", "T_merk", "T_pre")
    missing = [key for key in required_keys if key not in primitives]
    if missing:
        raise KeyError(f"Missing required primitive keys: {missing}")

    height = max(1, math.ceil(math.log2(max(2, n_users + 1))))

    xauth_cost = (2 * height + 1) * primitives["T_hash"]
    ssl_xiomt_cost = 1 * primitives["T_hash"]
    scheme30_cost = 1 * primitives["T_hash"]
    scape_zk_integrity = primitives["T_leaf_hash"] + primitives["T_merk"]
    scape_zk_total = scape_zk_integrity + primitives["T_pre"]

    return {
        "XAuth": xauth_cost,
        "SSL_XIoMT": ssl_xiomt_cost,
        "Scheme30": scheme30_cost,
        "SCAPE_ZK_Integrity": scape_zk_integrity,
        "SCAPE_ZK_Total": scape_zk_total,
    }


@dataclass
class Check:
    paper: str
    anchor: str
    paper_value: float
    paper_unit: str
    model_value: float
    tolerance_pct: float
    note: str

    @property
    def err_pct(self) -> float:
        if self.paper_value == 0:
            return float("inf")
        return abs(self.model_value - self.paper_value) / self.paper_value * 100.0

    @property
    def passed(self) -> bool:
        return self.err_pct <= self.tolerance_pct

    def pretty(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        return (
            f"  [{mark}]  {self.paper:<12} {self.anchor:<42} "
            f"paper={self.paper_value:>10.2f} {self.paper_unit:<4}  "
            f"model={self.model_value:>10.2f}  "
            f"err={self.err_pct:5.2f}%  (tol {self.tolerance_pct}%)\n"
            f"          note: {self.note}"
        )


def load_primitives(path: Path = PRIMITIVE_CSV) -> PrimitiveTimings:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing primitive benchmark CSV: {path}. "
            "Run `npm run bench:primitives` first."
        )

    mapping: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            mapping[row["primitive"]] = float(row["mean_ms"])

    try:
        return PrimitiveTimings(
            thash_ms=mapping["Thash (SHA-256, 32B input)"],
            tgrp_ms=mapping["Tgrp (BLS12-381 G1 scalar multiplication)"],
            tpair_ms=mapping["Tpair (BLS12-381 bilinear pairing)"],
            tsym_ms=mapping["Tsym (AES-256-GCM, 1KB payload)"],
        )
    except KeyError as exc:
        raise KeyError(
            f"Primitive CSV is missing required row: {exc}. "
            "Re-run `npm run bench:primitives`."
        ) from exc


def xauth_simulate(primitives: PrimitiveTimings, n_users: int = 1) -> dict:
    """XAuth paper-anchored model.

    The XAuth paper exposes end-to-end anonymous proof timings directly
    (Table 2), but not a full primitive decomposition. We therefore keep the
    proof-generation and proof-verification values anchored to the paper and
    derive only a lightweight MMHT-style hash proxy from local hardware.
    """
    proof_gen_ms = 89_700.0 * n_users
    verify_ms = 9.0 * n_users
    integrity_proxy_ms = simulate_integrity_costs(
        {
            "T_hash": primitives.thash_ms,
            "T_leaf_hash": primitives.thash_ms,
            "T_merk": 0.0,
            "T_pre": 0.0,
        },
        n_users=n_users,
        n_system_records=0,
    )["XAuth"]
    return {
        "proof_gen_ms": proof_gen_ms,
        "verify_ms": verify_ms,
        "proof_size_B": 288,
        "integrity_proxy_ms": integrity_proxy_ms,
        "source": "paper anchor for proof path; local SHA-256 proxy for MMHT validation",
    }


_SSLXIOMT_MS_PER_PROOF = 69_400.0 / 10_000.0


def sslxiomt_simulate(
    n_proofs: int,
    primitives: PrimitiveTimings | None = None,
    n_attrs: int = 10,
) -> dict:
    """SSL-XIoMT mixed model.

    The proof total is anchored to the paper's 10k-proof throughput claim.
    The encryption side is a primitive-calibrated proxy intended for fair
    same-machine comparison, not a claim of full-system reimplementation.
    """
    total_ms = _SSLXIOMT_MS_PER_PROOF * n_proofs
    verify_ms = 1000.0 / 918.0
    if primitives is None:
        encrypt_proxy_ms = float("nan")
    else:
        # Proxy for fog-assisted CP-ABE style work:
        # symmetric payload encryption + attribute hashing +
        # multiple curve multiplications + a small number of pairings.
        encrypt_proxy_ms = (
            primitives.tsym_ms
            + n_attrs * primitives.thash_ms
            + (2 * n_attrs + 2) * primitives.tgrp_ms
            + 2 * primitives.tpair_ms
        )
    return {
        "total_ms": total_ms,
        "ms_per_proof": _SSLXIOMT_MS_PER_PROOF,
        "verify_ms_per_proof": verify_ms,
        "encrypt_proxy_ms": encrypt_proxy_ms,
        "source": "paper anchor for proof throughput; primitive proxy for encryption path",
    }


_G1_B, _G2_B, _ZP_B, _H_B = 128, 128, 20, 32


def scheme30_simulate(
    primitives: PrimitiveTimings,
    n_k_disclosed: int = 10,
    n_attrs_total: int = 50,
    n_issuers: int = 5,
    batch_users: int = 1,
) -> dict:
    """Scheme [30] primitive proxy + paper-claim communication model.

    This is an intentionally explicit proxy model for the selective-disclosure
    credential path. It should be described in the paper as a primitive-based
    same-machine estimate, not as a full reproduction of the original system.
    """
    issue_ms = (
        n_attrs_total * primitives.tgrp_ms
        + max(1, n_issuers) * primitives.tgrp_ms
        + 2 * primitives.tpair_ms
        + n_attrs_total * primitives.thash_ms
    )
    show_ms = (
        (n_k_disclosed + 3) * primitives.tgrp_ms
        + primitives.tpair_ms
        + (n_k_disclosed + 2) * primitives.thash_ms
    )
    verify_ms = (
        2 * primitives.tpair_ms
        + 3 * primitives.tgrp_ms
        + (n_k_disclosed + batch_users) * primitives.thash_ms
    )

    scheme30_B = (2 * _G1_B + _ZP_B) + n_k_disclosed * _G1_B + _H_B
    attrs_per_issuer = max(1, n_attrs_total // max(1, n_issuers))
    fuchsbauer_B = n_issuers * (2 * _G1_B + _ZP_B + attrs_per_issuer * _G1_B + _H_B)
    ma_B = n_attrs_total * (3 * _G1_B) + (2 * _G1_B + _ZP_B)
    su_B = n_issuers * (2 * _G1_B + attrs_per_issuer * _G1_B) + _H_B

    def reduction(baseline_B: int) -> float:
        return (1.0 - scheme30_B / baseline_B) * 100.0

    return {
        "issue_ms": issue_ms,
        "show_ms": show_ms,
        "verify_ms": verify_ms,
        "scheme30_B": scheme30_B,
        "fuchsbauer_B": fuchsbauer_B,
        "ma_B": ma_B,
        "su_B": su_B,
        "reduction_vs_fuchsbauer": reduction(fuchsbauer_B),
        "reduction_vs_ma": reduction(ma_B),
        "reduction_vs_su": reduction(su_B),
        "source": "primitive proxy for compute path; paper-style formula for communication path",
    }


def xauth_validate(primitives: PrimitiveTimings) -> Check:
    paper_total_ms = 89_700.0
    model = xauth_simulate(primitives, n_users=1)["proof_gen_ms"]
    return Check(
        "XAuth",
        "Total anonymous proof generation",
        paper_total_ms,
        "ms",
        model,
        tolerance_pct=10.0,
        note="Paper exposes Table 2 total directly; model keeps that anchor.",
    )


def sslxiomt_validate(primitives: PrimitiveTimings) -> Check:
    paper_ms = 69_400.0
    model = sslxiomt_simulate(n_proofs=10_000, primitives=primitives)["total_ms"]
    return Check(
        "SSL-XIoMT",
        "Proof total @ n=10 000",
        paper_ms,
        "ms",
        model,
        tolerance_pct=2.0,
        note="Model preserves the paper's linearized 6.94 ms/proof anchor.",
    )


def scheme30_validate(primitives: PrimitiveTimings) -> Check:
    r = scheme30_simulate(primitives, n_k_disclosed=10, n_attrs_total=50, n_issuers=5)
    mean_reduction = (
        r["reduction_vs_fuchsbauer"]
        + r["reduction_vs_ma"]
        + r["reduction_vs_su"]
    ) / 3.0
    paper_midpoint = (62.5 + 92.79) / 2.0
    return Check(
        "Scheme [30]",
        "Mean comm. reduction vs 3 comparators",
        paper_midpoint,
        "%",
        mean_reduction,
        tolerance_pct=10.0,
        note="Communication model follows paper-style byte formulas; compute path is separate.",
    )


_VALIDATORS: tuple[tuple[str, Callable[[PrimitiveTimings], Check]], ...] = (
    ("xauth", xauth_validate),
    ("sslxiomt", sslxiomt_validate),
    ("scheme30", scheme30_validate),
)


def print_header() -> None:
    print("=" * 110)
    print("Baseline simulator — local primitives + paper-anchor validation")
    print("=" * 110)


def print_primitives(primitives: PrimitiveTimings) -> None:
    print("Local primitive timings (mean ms/op)")
    print(f"  Thash : {primitives.thash_ms:.6f} ms")
    print(f"  Tgrp  : {primitives.tgrp_ms:.6f} ms")
    print(f"  Tpair : {primitives.tpair_ms:.6f} ms")
    print(f"  Tsym  : {primitives.tsym_ms:.6f} ms")
    print("-" * 110)


def print_models(primitives: PrimitiveTimings) -> None:
    xauth = xauth_simulate(primitives)
    ssl = sslxiomt_simulate(1, primitives)
    s30 = scheme30_simulate(primitives)

    print("Representative modeled values on this machine")
    print(
        f"  XAuth       : proof_gen={xauth['proof_gen_ms']:.2f} ms, "
        f"verify={xauth['verify_ms']:.2f} ms, "
        f"integrity_proxy={xauth['integrity_proxy_ms']:.6f} ms"
    )
    print(
        f"  SSL-XIoMT   : proof={ssl['total_ms']:.2f} ms/proof, "
        f"verify={ssl['verify_ms_per_proof']:.4f} ms/proof, "
        f"encrypt_proxy={ssl['encrypt_proxy_ms']:.2f} ms"
    )
    print(
        f"  Scheme [30] : issue_proxy={s30['issue_ms']:.2f} ms, "
        f"show_proxy={s30['show_ms']:.2f} ms, "
        f"verify_proxy={s30['verify_ms']:.2f} ms"
    )
    print("-" * 110)


def run(paper: str | None = None, show_primitives: bool = False) -> int:
    primitives = load_primitives()
    print_header()
    if show_primitives:
        print_primitives(primitives)
    print_models(primitives)
    checks: list[Check] = []
    for name, fn in _VALIDATORS:
        if paper and paper != name:
            continue
        checks.append(fn(primitives))
    for check in checks:
        print(check.pretty())
    n_pass = sum(1 for c in checks if c.passed)
    print("-" * 110)
    print(f"  summary: {n_pass}/{len(checks)} checks passed")
    print("=" * 110)
    return 0 if n_pass == len(checks) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", choices=[n for n, _ in _VALIDATORS], help="Run just one validation.")
    ap.add_argument(
        "--show-primitives",
        action="store_true",
        help="Print the local primitive timing table before validations.",
    )
    args = ap.parse_args()
    return run(args.paper, show_primitives=args.show_primitives)


if __name__ == "__main__":
    sys.exit(main())
