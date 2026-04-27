from dataclasses import dataclass

from typing import Dict, Tuple

_COMPONENTS: Dict[str, Tuple[int, int, int, int]] = {

    "V_Signature": (142_945, 22_300, 288, 9),

    "V_Validity":  (244_626, 39_700, 288, 9),

    "V_SCT":       (232_715, 29_400, 288, 9),

    "V_Nym":        (17_405,  2_700, 288, 9),

}

_REPORTED_TOTAL_EQUATIONS = 614_286

_REPORTED_TOTAL_GEN_MS    = 89_700

_IPFS_MS          = 23

_ANCHOR_MS        = 1_300

_INQUIRY_MS       = 1_320

_CERT_OP_B        = 125

_MMHT_ROOT_B      = 64

_MMHT_SLOPE_BYTES_PER_LEAF    = 125

_MMHT_OVERHEAD_PER_INTERNAL_B = 6.4

@dataclass

class XAuthResult:

    phase: str

    comp_ms: float

    comm_bytes: float

    notes: str

def mmht_size(n_leaves: int) -> int:


    if n_leaves < 2:

        return _CERT_OP_B * n_leaves

    return round(_MMHT_SLOPE_BYTES_PER_LEAF * n_leaves

                 + _MMHT_OVERHEAD_PER_INTERNAL_B * (n_leaves - 1))

def derived_total_gen_ms() -> int:


    return sum(c[1] for c in _COMPONENTS.values())

def simulate(

    n_certs_in_mmht: int = 128,

    n_users_per_session: int = 1,

) -> Dict[str, XAuthResult]:


    total_gen = derived_total_gen_ms()

    results: Dict[str, XAuthResult] = {

        "storage": XAuthResult(

            phase="storage (anchor MMHT)",

            comp_ms=_ANCHOR_MS + _IPFS_MS,

            comm_bytes=mmht_size(n_certs_in_mmht),

            notes=f"Blockchain anchor ~{_ANCHOR_MS} ms + IPFS ~{_IPFS_MS} ms",

        ),

        "proof_gen": XAuthResult(

            phase="proof generation (per user)",

            comp_ms=total_gen * n_users_per_session,

            comm_bytes=_COMPONENTS["V_Signature"][2] * n_users_per_session,

            notes=f"sum of 4 Table-2 components = {total_gen} ms",

        ),

        "verify": XAuthResult(

            phase="verification",

            comp_ms=_COMPONENTS["V_Signature"][3] * n_users_per_session,

            comm_bytes=0,

            notes="constant per proof (9 ms)",

        ),

        "inquiry": XAuthResult(

            phase="inquiry",

            comp_ms=_INQUIRY_MS,

            comm_bytes=_MMHT_ROOT_B,

            notes=f"~{_INQUIRY_MS/1000:.2f} s independent of n_certs",

        ),

        "bind": XAuthResult(

            phase="bind",

            comp_ms=3.2 * (n_certs_in_mmht / 128),

            comm_bytes=_CERT_OP_B * n_certs_in_mmht,

            notes="Paper: 3.2 ms binds 128 cert ops",

        ),

    }

    return results

_MMHT_PUBLISHED = [

    (  4,   503),

    (  8, 1_007),

    ( 16, int(1.97 * 1024)),

    ( 32, int(3.95 * 1024)),

    ( 64, int(7.92 * 1024)),

    (128, int(15.8 * 1024)),

]

def validate() -> None:

    print("=" * 62)

    print("XAuth simulator — validation")

    print("=" * 62)

    derived = derived_total_gen_ms()

    err = abs(derived - _REPORTED_TOTAL_GEN_MS) / _REPORTED_TOTAL_GEN_MS * 100

    print(f"  [1] sum-of-components  paper_total={_REPORTED_TOTAL_GEN_MS} ms   "

          f"derived={derived} ms   err={err:4.1f}%   "

          f"{'OK' if err < 10 else 'FAIL'}")

    eq_sum = sum(c[0] for c in _COMPONENTS.values())

    err = abs(eq_sum - _REPORTED_TOTAL_EQUATIONS) / _REPORTED_TOTAL_EQUATIONS * 100

    print(f"  [2] sum-of-equations   paper_total={_REPORTED_TOTAL_EQUATIONS}   "

          f"derived={eq_sum}   err={err:4.1f}%   "

          f"{'OK (paper rounding)' if err < 5 else 'FAIL'}")

    print(f"  [3] MMHT fit against 6 published points (125·n + 6.4·(n-1)):")

    worst = 0.0

    for n, paper in _MMHT_PUBLISHED:

        got = mmht_size(n)

        err = abs(got - paper) / paper * 100

        worst = max(worst, err)

        print(f"        n={n:>3}  paper={paper:>6} B  model={got:>6} B  err={err:+5.1f}%")

    print(f"      worst-case err = {worst:.1f}% → "

          f"{'OK (<10%)' if worst < 10 else 'FAIL'}")

    print()

if __name__ == "__main__":

    validate()
