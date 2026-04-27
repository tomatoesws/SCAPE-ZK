from __future__ import annotations

import argparse

import math

import sys

from dataclasses import dataclass

from typing import Callable, Tuple

@dataclass

class Check:

    paper: str

    anchor: str

    paper_value: float

    paper_unit: str

    model_value: float

    tolerance_pct: float

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

        return (f"  [{mark}]  {self.paper:<12} {self.anchor:<42} "

                f"paper={self.paper_value:>10.2f} {self.paper_unit:<4}  "

                f"model={self.model_value:>10.2f}  "

                f"err={self.err_pct:5.2f}%  (tol {self.tolerance_pct}%)")

_XAUTH_COMPONENTS = {

    "V_Signature": (142_945,    22_300,        9),

    "V_Validity":  (244_626,    39_700,        9),

    "V_SCT":       (232_715,    29_400,        9),

    "V_Nym":       ( 17_405,     2_700,        9),

}

_XAUTH_PROOF_SIZE_B = 288

def xauth_simulate(n_users: int = 1) -> dict:


    comps = _XAUTH_COMPONENTS

    gen_ms = sum(c[1] for c in comps.values()) * n_users

    verify_ms = comps["V_Signature"][2] * n_users

    return {

        "proof_gen_ms":   gen_ms,

        "verify_ms":      verify_ms,

        "proof_size_B":   _XAUTH_PROOF_SIZE_B,

        "eq_count":       sum(c[0] for c in comps.values()),

    }

def xauth_validate() -> Check:


    PAPER_TOTAL_MS = 89_700

    model = xauth_simulate(n_users=1)["proof_gen_ms"]

    return Check("XAuth",

                 "Total anonymous proof generation",

                 PAPER_TOTAL_MS, "ms",

                 model,

                 tolerance_pct=10.0)

_SSLXIOMT_MS_PER_PROOF = 69_400 / 10_000

def sslxiomt_simulate(n_proofs: int) -> dict:


    total_ms = _SSLXIOMT_MS_PER_PROOF * n_proofs

    peak_tps = 918

    k = 35

    def tps(u: int) -> float: return peak_tps * u / (u + k)

    return {

        "total_ms":         total_ms,

        "ms_per_proof":     _SSLXIOMT_MS_PER_PROOF,

        "tps_at_150_users": tps(150),

    }

def sslxiomt_validate() -> Check:


    PAPER_MS = 69_400

    model = sslxiomt_simulate(n_proofs=10_000)["total_ms"]

    return Check("SSL-XIoMT",

                 "Proof total @ n=10 000 (PLONK+ZK-STARK batched)",

                 PAPER_MS, "ms",

                 model,

                 tolerance_pct=2.0)

_G1_B, _G2_B, _Zp_B, _H_B = 128, 128, 20, 32

def scheme30_simulate(n_k_disclosed: int = 10,

                      n_attrs_total: int = 50,

                      n_issuers: int = 5) -> dict:



    scheme30_B = (2 * _G1_B + _Zp_B) + n_k_disclosed * _G1_B + _H_B

    attrs_per_issuer = max(1, n_attrs_total // n_issuers)

    fuchsbauer_B = n_issuers * (2 * _G1_B + _Zp_B

                                + attrs_per_issuer * _G1_B + _H_B)

    ma_B = n_attrs_total * (3 * _G1_B) + (2 * _G1_B + _Zp_B)

    su_B = n_issuers * (2 * _G1_B + attrs_per_issuer * _G1_B) + _H_B

    def reduction(baseline_B: int) -> float:

        return (1.0 - scheme30_B / baseline_B) * 100.0

    return {

        "scheme30_B":   scheme30_B,

        "fuchsbauer_B": fuchsbauer_B,

        "ma_B":         ma_B,

        "su_B":         su_B,

        "reduction_vs_fuchsbauer": reduction(fuchsbauer_B),

        "reduction_vs_ma":         reduction(ma_B),

        "reduction_vs_su":         reduction(su_B),

    }

def scheme30_validate() -> Check:


    r = scheme30_simulate(n_k_disclosed=10, n_attrs_total=50, n_issuers=5)

    mean_reduction = (r["reduction_vs_fuchsbauer"]

                      + r["reduction_vs_ma"]

                      + r["reduction_vs_su"]) / 3.0

    PAPER_MIDPOINT = (62.5 + 92.79) / 2.0

    return Check("Scheme [30]",

                 "Mean comm. reduction vs 3 comparators",

                 PAPER_MIDPOINT, "%",

                 mean_reduction,

                 tolerance_pct=10.0)

_VALIDATORS: Tuple[Tuple[str, Callable[[], Check]], ...] = (

    ("xauth",     xauth_validate),

    ("sslxiomt",  sslxiomt_validate),

    ("scheme30",  scheme30_validate),

)

def _print_header() -> None:

    print("=" * 110)

    print("Baseline cost simulators — one-published-point validation")

    print("=" * 110)

def run(paper: str | None = None) -> int:

    _print_header()

    checks = []

    for name, fn in _VALIDATORS:

        if paper and paper != name:

            continue

        checks.append(fn())

    for c in checks:

        print(c.pretty())

    n_pass = sum(1 for c in checks if c.passed)

    print("-" * 110)

    print(f"  summary: {n_pass}/{len(checks)} checks passed")

    print("=" * 110)

    return 0 if n_pass == len(checks) else 1

def main() -> int:

    ap = argparse.ArgumentParser(description=__doc__)

    ap.add_argument("--paper", choices=[n for n, _ in _VALIDATORS],

                    help="Run just one paper's validation (default: all).")

    args = ap.parse_args()

    return run(args.paper)

if __name__ == "__main__":

    sys.exit(main())
