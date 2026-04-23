
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Data from previous turn (Table 4 summary)
B = [1, 10, 50, 100, 200]

# Verification Latency (ms) vs Batch Size (B)
# SCAPE-ZK: Constant ~15ms (from bls_bench.csv pairing_only mean)
# Scheme [30]: aggregate verify (from bls_bench.csv verify_agg mean)
# XAuth [6]: Linear 9ms/user (from paper: 9ms for 1 user)
# SSL-XIoMT [8]: Linear 1.09ms/user (from paper: 918 tps -> 1000/918 = 1.089 ms)

scape_zk_v = [15.0, 15.0, 15.0, 15.0, 15.0] # Constant O(1)
scheme_30_v = [20.8, 70.9, 297.8, 566.9, 1128.0] # O(B)
xauth_v = [9 * b for b in B] # O(B)
ssl_xiomt_v = [1.089 * b for b in B] # O(B)

plt.figure(figsize=(10, 6))

plt.plot(B, scape_zk_v, label='SCAPE-ZK (Ours, $O(1)$)', marker='o', linewidth=3, color='#1a5490')
plt.plot(B, scheme_30_v, label='Scheme [30] ($O(B)$)', marker='s', linestyle='--', color='#e89b00')
plt.plot(B, xauth_v, label='XAuth [6] ($O(B)$)', marker='^', linestyle=':', color='#c84130')
plt.plot(B, ssl_xiomt_v, label='SSL-XIoMT [8] ($O(B)$)', marker='x', linestyle='-.', color='#2ca02c')

plt.title('On-chain Verification Latency vs. Batch Size (B)')
plt.xlabel('Batch Size / Concurrent Users (B)')
plt.ylabel('Verification Time (ms)')
plt.yscale('log') # Use log scale because XAuth is much higher at large B
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.legend()

OUT = Path.home() / "scape-zk" / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT / "verification_comparison_log.png")

# Linear plot for more intuitive view of low B
plt.figure(figsize=(10, 6))
plt.plot(B, scape_zk_v, label='SCAPE-ZK (Ours, $O(1)$)', marker='o', linewidth=3, color='#1a5490')
plt.plot(B, scheme_30_v, label='Scheme [30] ($O(B)$)', marker='s', linestyle='--', color='#e89b00')
plt.plot(B, xauth_v, label='XAuth [6] ($O(B)$)', marker='^', linestyle=':', color='#c84130')
plt.plot(B, ssl_xiomt_v, label='SSL-XIoMT [8] ($O(B)$)', marker='x', linestyle='-.', color='#2ca02c')

plt.title('On-chain Verification Latency vs. Batch Size (B)')
plt.xlabel('Batch Size / Concurrent Users (B)')
plt.ylabel('Verification Time (ms)')
plt.grid(True, alpha=0.5)
plt.legend()
plt.savefig(OUT / "verification_comparison_linear.png")

print(f"Graphs saved to {OUT}")
