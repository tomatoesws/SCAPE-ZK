"""
SCAPE-ZK — CP-ABE and Symmetric Encryption Benchmark
Member A scope. Fills the 'Encrypt' column of Table IV:
  SCAPE-ZK requires T^sym_enc + T^abe_enc per record.

Measures Charm-Crypto BSW07 CP-ABE + AES-256-GCM.
Sweeps attribute counts {5, 10, 20, 50} per experimental_params.md.

Output: results/cpabe_bench.csv
"""
import time
import statistics
import csv
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone

from charm.toolbox.pairinggroup import PairingGroup, GT
from charm.schemes.abenc.abenc_bsw07 import CPabe_BSW07
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
CSV_OUT = ROOT / "results" / "cpabe_bench.csv"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

ATTR_COUNTS = [5, 10, 20, 50]
RUNS = 20
WARMUP = 3

def time_op(fn, runs=RUNS, warmup=WARMUP):
    """Run fn() (runs+warmup) times; return stats over the measured runs."""
    times = []
    for i in range(runs + warmup):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        if i >= warmup:
            times.append((t1 - t0) * 1000.0)  # ms
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

# -- Initialize pairing group and BSW07 scheme (curve SS512: symmetric bilinear) --
print("Initializing Charm-Crypto BSW07 CP-ABE on curve SS512...")
group = PairingGroup("SS512")
cpabe = CPabe_BSW07(group)

# ----------- Setup (one-time system-wide) -----------
print("\n=== Setup (one-time system parameters) ===")
def do_setup():
    return cpabe.setup()
setup_stats = time_op(do_setup, runs=10, warmup=2)
print(f"setup:        {fmt(setup_stats)}")
pk_master, mk_master = cpabe.setup()

# --- Per-attribute-count sweep ---
results_rows = []

for N in ATTR_COUNTS:
    print(f"\n=== N = {N} attributes ===")
    attrs = [f"ATTR{i}" for i in range(N)]
    # Policy: conjunction of all N attributes (worst-case for BSW07 complexity)
    policy = " and ".join(attrs)

    # ----------- Keygen (per-user, depends on attribute count) -----------
    def do_keygen():
        return cpabe.keygen(pk_master, mk_master, attrs)
    keygen_stats = time_op(do_keygen)
    print(f"keygen({N:>2}):  {fmt(keygen_stats)}")
    sk_user = cpabe.keygen(pk_master, mk_master, attrs)

    # ----------- CP-ABE encrypt (of a random GT element — the session key) -----------
    # In a hybrid scheme, CP-ABE encrypts a symmetric key, not the data itself.
    msg_gt = group.random(GT)
    def do_cpabe_encrypt():
        return cpabe.encrypt(pk_master, msg_gt, policy)
    cpabe_enc_stats = time_op(do_cpabe_encrypt)
    print(f"cpabe_enc:    {fmt(cpabe_enc_stats)}")

    # ----------- CP-ABE decrypt -----------
    ct_abe = cpabe.encrypt(pk_master, msg_gt, policy)
    def do_cpabe_decrypt():
        return cpabe.decrypt(pk_master, sk_user, ct_abe)
    cpabe_dec_stats = time_op(do_cpabe_decrypt)
    print(f"cpabe_dec:    {fmt(cpabe_dec_stats)}")

    # Verify correctness once
    recovered = cpabe.decrypt(pk_master, sk_user, ct_abe)
    assert recovered == msg_gt, "CP-ABE decrypt correctness failed!"

    # ----------- Symmetric encryption (AES-256-GCM) -----------
    # This is T^sym_enc — encrypting the actual EHR payload under the symmetric key.
    # We time encrypt on a representative 1 KB payload (typical EHR field size;
    # report result as "per-KB" and note that scales linearly for larger payloads).
    sym_key = secrets.token_bytes(32)
    aes = AESGCM(sym_key)
    nonce = secrets.token_bytes(12)
    plaintext = secrets.token_bytes(1024)  # 1 KB payload
    aad = b"scape-zk-aad"
    def do_sym_encrypt():
        return aes.encrypt(nonce, plaintext, aad)
    sym_enc_stats = time_op(do_sym_encrypt, runs=50, warmup=5)  # fast op, more runs
    print(f"sym_enc(1KB): {fmt(sym_enc_stats)}")

    # ----------- SCAPE-ZK 'Encrypt' total per Table IV: T^sym + T^abe -----------
    total = sym_enc_stats["mean"] + cpabe_enc_stats["mean"]
    print(f"  => SCAPE-ZK Encrypt (sym + abe): {total:7.3f} ms")

    ts = datetime.now(timezone.utc).isoformat()
    for op_name, s in [
        ("setup", setup_stats),           # same for every N
        ("keygen", keygen_stats),
        ("cpabe_encrypt", cpabe_enc_stats),
        ("cpabe_decrypt", cpabe_dec_stats),
        ("sym_encrypt_1KB", sym_enc_stats),
    ]:
        results_rows.append({
            "timestamp": ts, "n_attrs": N, "operation": op_name,
            "n_runs": s["n"], "mean_ms": round(s["mean"], 4),
            "std_ms": round(s["std"], 4), "median_ms": round(s["median"], 4),
            "min_ms": round(s["min"], 4), "max_ms": round(s["max"], 4),
        })

# ----------- Write CSV -----------
is_new = not CSV_OUT.exists()
with open(CSV_OUT, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "timestamp", "n_attrs", "operation", "n_runs",
        "mean_ms", "std_ms", "median_ms", "min_ms", "max_ms"
    ])
    if is_new:
        writer.writeheader()
    for r in results_rows:
        writer.writerow(r)

# ----------- Summary table -----------
print("\n" + "=" * 72)
print("SUMMARY — SCAPE-ZK Encrypt column of Table IV (T^sym_enc + T^abe_enc)")
print("=" * 72)
print(f"{'N':>4}  {'T^abe_enc (ms)':>16}  {'T^sym_enc (ms)':>16}  {'Total (ms)':>12}")
print("-" * 72)
by_n = {}
for r in results_rows:
    by_n.setdefault(r["n_attrs"], {})[r["operation"]] = r["mean_ms"]
for N in ATTR_COUNTS:
    abe = by_n[N]["cpabe_encrypt"]
    sym = by_n[N]["sym_encrypt_1KB"]
    print(f"{N:>4}  {abe:>16.3f}  {sym:>16.3f}  {abe + sym:>12.3f}")
print(f"\nFull results saved to: {CSV_OUT}")
