"""
SCAPE-ZK — Proxy Re-Encryption Benchmark (AFGH06, inline impl.)
Member A scope. Fills the delegation timing for Phase 4 of the paper.

Bypasses Charm-Crypto's buggy pre_afgh06 API by implementing the scheme
inline. Math is the standard AFGH06 first-level/second-level construction.

Note on curve: SS512 is used (same as CP-ABE benchmark) for implementation
consistency. SS512 provides ~80-bit security; production would use BN254.
This is documented in experimental_params.md.

Operations timed (per paper's Phase 4):
  - encrypt:       DO encrypts to themselves (Phase 1 CTk setup)
  - rekeygen:      DO generates delegation key (Phase 4 Step 2)
  - re_encrypt:    Fog node transforms ciphertext (Phase 4 Step 3) — THE KEY METRIC
  - decrypt_re:    DU decrypts transformed ciphertext (Phase 5 Step 5)

Output: results/pre_bench.csv
"""
import time
import statistics
import csv
from pathlib import Path
from datetime import datetime, timezone

from charm.toolbox.pairinggroup import PairingGroup, GT, G1, ZR, pair

ROOT = Path(__file__).resolve().parents[1]
CSV_OUT = ROOT / "results" / "pre_bench.csv"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

RUNS = 30
WARMUP = 3


# =========================================================
# Inline AFGH06 PRE Scheme
# =========================================================
class PreAFGH06:
    def __init__(self, group):
        self.group = group

    def setup(self):
        g = self.group.random(G1)
        Z = pair(g, g)
        return {'g': g, 'Z': Z}

    def keygen(self, params):
        sk = self.group.random(ZR)
        pk = params['g'] ** sk
        return pk, sk

    def encrypt(self, params, pk, m):
        r = self.group.random(ZR)
        c1 = pk ** r
        c2 = m * (params['Z'] ** r)
        return {'c1': c1, 'c2': c2}

    def rekeygen(self, params, sk_a, pk_b):
        return pk_b ** (~sk_a)

    def re_encrypt(self, params, rk, c_a):
        c1_prime = pair(c_a['c1'], rk)
        return {'c1_prime': c1_prime, 'c2': c_a['c2']}

    def decrypt(self, params, sk, c):
        if 'c1_prime' in c:
            Z_r = c['c1_prime'] ** (~sk)
            return c['c2'] / Z_r
        else:
            Z_r = pair(c['c1'], params['g']) ** (~sk)
            return c['c2'] / Z_r


# =========================================================
# Benchmark harness
# =========================================================
def time_op(fn, runs=RUNS, warmup=WARMUP):
    times = []
    for i in range(runs + warmup):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        if i >= warmup:
            times.append((t1 - t0) * 1000)
    n = len(times)
    mean = statistics.mean(times)
    std = statistics.stdev(times) if n > 1 else 0.0
    srt = sorted(times)
    return {
        "n": n, "mean": mean, "std": std,
        "median": srt[n // 2],
        "min": srt[0], "max": srt[-1],
    }


def fmt(s):
    return (f"mean={s['mean']:7.3f}ms  std={s['std']:6.3f}ms  "
            f"median={s['median']:7.3f}ms  (n={s['n']})")


# =========================================================
# Execution
# =========================================================
print("Initializing AFGH06 PRE (inline implementation) on curve SS512...")
group = PairingGroup("SS512")
pre = PreAFGH06(group)
params = pre.setup()

pk_DO, sk_DO = pre.keygen(params)
pk_DU, sk_DU = pre.keygen(params)
msg = group.random(GT)

# Correctness sanity check BEFORE benchmarking — abort early if the math is wrong
ct = pre.encrypt(params, pk_DO, msg)
recovered_direct = pre.decrypt(params, sk_DO, ct)
assert recovered_direct == msg, "Direct decrypt correctness FAILED"

rk = pre.rekeygen(params, sk_DO, pk_DU)
ct_re = pre.re_encrypt(params, rk, ct)
recovered_re = pre.decrypt(params, sk_DU, ct_re)
assert recovered_re == msg, "Re-encrypt decrypt correctness FAILED"
print("Correctness checks passed.\n")

# --- Time each operation ---
print("=== Operation timings ===")

def do_encrypt():
    return pre.encrypt(params, pk_DO, msg)
enc_stats = time_op(do_encrypt)
print(f"encrypt:        {fmt(enc_stats)}")

def do_rekeygen():
    return pre.rekeygen(params, sk_DO, pk_DU)
rkg_stats = time_op(do_rekeygen)
print(f"rekeygen:       {fmt(rkg_stats)}")

# For re_encrypt, we use the pre-computed rk and ct so only the transform is timed
def do_reencrypt():
    return pre.re_encrypt(params, rk, ct)
reenc_stats = time_op(do_reencrypt)
print(f"re_encrypt:     {fmt(reenc_stats)}   <-- Fog node cost (Phase 4 Step 3)")

def do_decrypt_re():
    return pre.decrypt(params, sk_DU, ct_re)
dec_stats = time_op(do_decrypt_re)
print(f"decrypt_re:     {fmt(dec_stats)}   <-- DU cost (Phase 5 Step 5)")

# --- CSV output matching your project convention ---
ts = datetime.now(timezone.utc).isoformat()
rows = []
for op_name, s in [
    ("encrypt", enc_stats),
    ("rekeygen", rkg_stats),
    ("re_encrypt", reenc_stats),
    ("decrypt_re", dec_stats),
]:
    rows.append({
        "timestamp": ts, "operation": op_name,
        "n_runs": s["n"], "mean_ms": round(s["mean"], 4),
        "std_ms": round(s["std"], 4), "median_ms": round(s["median"], 4),
        "min_ms": round(s["min"], 4), "max_ms": round(s["max"], 4),
    })

is_new = not CSV_OUT.exists()
with open(CSV_OUT, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "timestamp", "operation", "n_runs",
        "mean_ms", "std_ms", "median_ms", "min_ms", "max_ms"
    ])
    if is_new:
        writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"\nResults saved to: {CSV_OUT}")
