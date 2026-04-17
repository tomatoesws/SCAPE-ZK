import subprocess, time, statistics
from pathlib import Path

HOME = Path.home() / "scape-zk"

def time_cmd(cmd, runs=10, warmup=1):
    """Run cmd N times, drop warmups, return (mean_ms, std_ms, all_times)."""
    times = []
    for i in range(runs + warmup):
        t0 = time.perf_counter()
        subprocess.run(cmd, shell=True, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t1 = time.perf_counter()
        if i >= warmup:
            times.append((t1 - t0) * 1000)
    mean = statistics.mean(times)
    std = statistics.stdev(times) if len(times) > 1 else 0.0
    return mean, std, times

if __name__ == "__main__":
    zkey = HOME / "keys" / "multiplier_final.zkey"
    wtns = HOME / "circuits" / "witness.wtns"
    proof = HOME / "proofs" / "proof.json"
    public = HOME / "proofs" / "public.json"
    vkey = HOME / "keys" / "verification_key.json"

    # Make sure output dir exists
    proof.parent.mkdir(parents=True, exist_ok=True)

    prove_cmd = f"snarkjs groth16 prove {zkey} {wtns} {proof} {public}"
    verify_cmd = f"snarkjs groth16 verify {vkey} {public} {proof}"

    print("Benchmarking Groth16 prove...")
    mean_p, std_p, _ = time_cmd(prove_cmd, runs=10)
    print(f"  Prove:  {mean_p:8.2f} ± {std_p:6.2f} ms  (10 runs)")

    print("Benchmarking Groth16 verify...")
    mean_v, std_v, _ = time_cmd(verify_cmd, runs=30)
    print(f"  Verify: {mean_v:8.2f} ± {std_v:6.2f} ms  (30 runs)")
