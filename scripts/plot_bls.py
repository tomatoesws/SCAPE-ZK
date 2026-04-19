import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path.home() / "scape-zk"
CSV = ROOT / "results" / "bls_bench.csv"
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV)
pair_df = df[df["operation"] == "pairing_only"].sort_values("batch_size")
agg_df = df[df["operation"] == "verify_agg"].sort_values("batch_size")
naive_df = df[df["operation"] == "verify_naive"].sort_values("batch_size")

batches = pair_df["batch_size"].values
COLORS = {"naive": "#c84130", "agg": "#e89b00", "pair": "#1a5490"}

# FIG A6
plt.figure(figsize=(7, 4.5))
plt.plot(batches, naive_df["mean_ms"], marker='o', label='O(n) Baseline (Naive Verify)', color=COLORS["naive"], linewidth=2)
plt.plot(batches, pair_df["mean_ms"], marker='s', label='SCAPE-ZK On-chain O(1)', color=COLORS["pair"], linewidth=2)
plt.title("On-Chain Verification Cost vs. Concurrent Requests")
plt.xlabel("Number of Requests (Batch Size n)")
plt.ylabel("Verification Time (ms)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
for ext in ['png', 'pdf']: plt.savefig(OUT / f"figA6_onchain_scalability.{ext}")
plt.close()

# FIG A7
plt.figure(figsize=(6, 5))
n200_pair = pair_df[pair_df["batch_size"] == 200]["mean_ms"].iloc[0]
n200_agg = agg_df[agg_df["batch_size"] == 200]["mean_ms"].iloc[0]
n200_naive = naive_df[naive_df["batch_size"] == 200]["mean_ms"].iloc[0]
n200_prep = n200_agg - n200_pair

bars = ["Baseline (Naive)", "SCAPE-ZK (Total)"]
onchain = [n200_naive, n200_pair]
offchain = [0, n200_prep]

plt.bar(bars, onchain, width=0.5, color=COLORS["pair"], label="On-Chain Cost (Pairing)")
plt.bar(bars, offchain, bottom=onchain, width=0.5, color=COLORS["agg"], label="Off-Chain Cost (Fog Preprocessing)")
plt.ylabel("Total Execution Time (ms) at n=200")
plt.title("Cost Delegation: Blockchain vs Fog Node (n=200)")
plt.legend()
for ext in ['png', 'pdf']: plt.savefig(OUT / f"figA7_cost_delegation.{ext}")
plt.close()
