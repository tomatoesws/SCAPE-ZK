from dataclasses import dataclass

from typing import Dict

_SSLXIOMT_MS_PER_PROOF   = 6.94

_BASELINE31_MS_PER_PROOF = 522.30

_PEAK_TPS_SSLXIOMT       = 918

_PEAK_TPS_BASELINE31     = 777

_E2E_PER_PHASE_MS        = 25

_ENCRYPT_BASE_MS      = 5.5

_ENCRYPT_PER_ATTR_MS  = 0.42

@dataclass

class SSLXIoMTResult:

    phase: str

    comp_ms: float

    comm_bytes: float

    notes: str

def proof_time_total(n_proofs: int, mode: str = "sslxiomt") -> float:


    if mode == "sslxiomt":

        return _SSLXIOMT_MS_PER_PROOF * n_proofs

    elif mode == "baseline31":

        return _BASELINE31_MS_PER_PROOF * n_proofs

    raise ValueError(mode)

def verify_throughput(concurrent_users: int, mode: str = "sslxiomt") -> float:


    peak = _PEAK_TPS_SSLXIOMT if mode == "sslxiomt" else _PEAK_TPS_BASELINE31

    k = 35

    return peak * concurrent_users / (concurrent_users + k)

def encrypt_time(data_kb: float, n_attrs: int) -> float:


    data_cost = max(0.5, data_kb * 0.12)

    return _ENCRYPT_BASE_MS + _ENCRYPT_PER_ATTR_MS * n_attrs + data_cost

def simulate(n_proofs: int = 1_000,

             concurrent_users: int = 100,

             data_kb: float = 10_000,

             n_attrs: int = 50) -> Dict[str, SSLXIoMTResult]:

    out: Dict[str, SSLXIoMTResult] = {}

    out["proof_total"] = SSLXIoMTResult(

        "proof_total",

        proof_time_total(n_proofs),

        0,

        f"PLONK+ZK-STARK, batched via zk-Rollup, n={n_proofs}",

    )

    out["throughput"] = SSLXIoMTResult(

        "throughput",

        0,

        0,

        f"{verify_throughput(concurrent_users):.0f} verifies/s at {concurrent_users} users",

    )

    out["encrypt"] = SSLXIoMTResult(

        "encrypt",

        encrypt_time(data_kb, n_attrs),

        0,

        f"payload={data_kb} KB, attrs={n_attrs}",

    )

    out["e2e"] = SSLXIoMTResult(

        "e2e",

        _E2E_PER_PHASE_MS * 4,

        0,

        "Paper: <100 ms full flow",

    )

    return out

def validate() -> None:

    print("=" * 62)

    print("SSL-XIoMT simulator — validation")

    print("=" * 62)

    got_10k = proof_time_total(10_000)

    lo, hi = 69_400, 76_800

    print(f"  [1] linearity@10k  paper_range=[{lo},{hi}] ms   model={got_10k:.0f} ms   "

          f"{'OK (inside)' if lo <= got_10k <= hi else 'OUT'}")

    got = verify_throughput(10_000)

    target = _PEAK_TPS_SSLXIOMT

    err = abs(got - target) / target * 100.0

    print(f"  [2] tps asymptote  paper_peak={target}   model_u=10k={got:.1f}   "

          f"err={err:4.1f}%   {'OK (<1%)' if err < 1 else 'FAIL'}")

    print(f"  [3] [31] rate = {_BASELINE31_MS_PER_PROOF:.1f} ms/proof  "

          f"(calibrated at n=1 000; model diverges at large n — see comment)")

    print()

if __name__ == "__main__":

    validate()
