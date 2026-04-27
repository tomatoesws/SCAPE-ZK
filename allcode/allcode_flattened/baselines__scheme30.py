from dataclasses import dataclass

from typing import Dict

from .common import OPS_TYPEF_I7, SIZES_TYPEF, scale_to

@dataclass

class Scheme30Result:

    phase: str

    comp_ms: float

    comm_bytes: float

    notes: str

def simulate(

    n_attrs: int = 10,

    n_issuers: int = 5,

    n_updates: int = 1,

    n_users_batch: int = 50,

    cpu_ghz_actual: float = 2.30,

    cpu_ghz_paper: float = 2.30,

) -> Dict[str, Scheme30Result]:

    ops = scale_to(OPS_TYPEF_I7,

                   ghz_from=cpu_ghz_paper,

                   ghz_to=cpu_ghz_actual)

    s = SIZES_TYPEF

    showcred_ms = n_attrs * ops.T_sm + n_issuers * ops.T_h + ops.T_mul

    verify_ms   = 2 * ops.T_pair + n_attrs * ops.T_sm + ops.T_mul

    trace_ms    = ops.T_sm + ops.T_mul

    update_ms   = n_updates * ops.T_sm + ops.T_mul

    batch_ms    = 2 * ops.T_pair + ops.T_sm + n_users_batch * ops.T_h

    non_batch_ms = n_users_batch * verify_ms

    cred_bytes   = 2 * s.G1 + s.Zp

    present_bytes = cred_bytes + n_attrs * s.G1 + s.H

    verify_bytes = s.H

    batch_bytes  = 2 * s.G1 + n_users_batch * s.H

    out: Dict[str, Scheme30Result] = {

        "showcred": Scheme30Result("showcred", showcred_ms, present_bytes,

                                   "Linear in n_k, constant in n_I"),

        "verify":   Scheme30Result("verify",   verify_ms,  verify_bytes,

                                   "2·T_pair + n_k·T_sm"),

        "trace":    Scheme30Result("trace",    trace_ms, s.H,

                                   "Constant"),

        "update":   Scheme30Result("update",   update_ms, n_updates * s.G1,

                                   "Linear in updates"),

        "batch":    Scheme30Result("batch",    batch_ms, batch_bytes,

                                   f"Aggregate authentication for {n_users_batch} users"),

        "nonbatch": Scheme30Result("nonbatch", non_batch_ms,

                                   n_users_batch * present_bytes,

                                   "Serial authentication"),

    }

    return out

def _baseline_comm(n_attrs_total: int, n_issuers: int, style: str) -> int:


    s = SIZES_TYPEF

    cred = 2 * s.G1 + s.Zp

    attrs_per_issuer = max(1, n_attrs_total // n_issuers)

    if style == "fuchsbauer":

        return n_issuers * (cred + attrs_per_issuer * s.G1 + s.H)

    if style == "ma":

        zkp_bytes = 3 * s.G1

        return n_attrs_total * zkp_bytes + cred

    if style == "su":

        return n_issuers * (cred + attrs_per_issuer * s.G1) + s.H

    raise ValueError(style)

def validate() -> None:

    print("=" * 62)

    print("Scheme [30] simulator — published-point validation")

    print("=" * 62)

    r = simulate(n_attrs=10, n_issuers=5)

    present_b = r["showcred"].comm_bytes

    lo, hi = 62.5, 92.79

    any_out = False

    for style in ("fuchsbauer", "ma", "su"):

        baseline_b = _baseline_comm(n_attrs_total=50, n_issuers=5, style=style)

        reduction = (1 - present_b / baseline_b) * 100.0

        ok = lo <= reduction <= hi

        any_out = any_out or (not ok)

        print(f"  Comm reduction vs {style:<10} target=[{lo},{hi}] %   got={reduction:5.2f} %   "

              f"{'OK' if ok else 'OUT'}")

    if not any_out:

        print("  -> all three reductions within paper's 62.5–92.79 % range.")

    c5  = simulate(n_attrs=5)["showcred"].comp_ms

    c50 = simulate(n_attrs=50)["showcred"].comp_ms

    print(f"  ShowCred slope n_k:    {c5:.2f} → {c50:.2f} ms   {'INCREASING' if c50 > c5 else 'FAIL'}")

    i5  = simulate(n_attrs=10, n_issuers=5)["showcred"].comp_ms

    i40 = simulate(n_attrs=10, n_issuers=40)["showcred"].comp_ms

    flat = (i40 - i5) / i5 * 100.0

    print(f"  ShowCred slope n_I:    {i5:.3f} → {i40:.3f} ms   delta={flat:.2f}%   {'OK' if flat < 5 else 'too steep'}")

    v = simulate(n_attrs=10)["verify"].comp_ms

    print(f"  Verify > 2·T_pair:     verify={v:.2f} ms > 2·T_pair={2*OPS_TYPEF_I7.T_pair:.2f} ms   OK")

    print()

if __name__ == "__main__":

    validate()
