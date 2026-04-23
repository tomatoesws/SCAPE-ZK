
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

# Parameters
N_attr = [5, 10, 20, 50]
B_size = [1, 10, 50, 100, 200]

# --- Convert all data from ms to seconds (/ 1000) ---
szk_gen = np.array([516.7, 544.2, 573.3, 831.8]) / 1000
xauth_gen = np.array([89700] * 4) / 1000
ssl_gen = np.array([7.6] * 4) / 1000
s30_gen = np.array([25, 35, 45, 65]) / 1000

szk_enc = np.array([15.2, 24.7, 47.1, 117.7]) / 1000
ssl_enc = np.array([10, 18, 30, 80]) / 1000

szk_ver = np.array([15] * 5) / 1000
s30_ver = np.array([20.8, 70.9, 297.8, 566.9, 1128.0]) / 1000
xauth_ver = np.array([9 * b for b in B_size]) / 1000
ssl_ver = np.array([1.09 * b for b in B_size]) / 1000

# Setup Figure
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
plt.subplots_adjust(hspace=0.35, wspace=0.25)

def format_log_axis(ax):
    ax.set_yscale('log')
    # Use ScalarFormatter to show real numbers instead of 10^x
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
    # Ensure some minor ticks are shown and formatted
    ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    ax.grid(True, which="major", ls="-", alpha=0.3)

# (1) Proof Generation
ax = axs[0, 0]
ax.plot(N_attr, szk_gen, 'o-', label='SCAPE-ZK', color='#1a5490', linewidth=2)
ax.plot(N_attr, s30_gen, 's--', label='Scheme [30]', color='#e89b00')
ax.plot(N_attr, ssl_gen, 'x-.', label='SSL-XIoMT (Amortized)', color='#2ca02c')
ax.plot(N_attr, xauth_gen, '^:', label='XAuth [6]', color='#c84130', linewidth=2)
ax.set_title("Phase 1: Proof Generation Cost vs. N")
ax.set_xlabel("Number of Attributes (N)")
ax.set_ylabel("Time (seconds)")
format_log_axis(ax)
ax.legend()

# (2) Proof Verification
ax = axs[0, 1]
ax.plot(B_size, szk_ver, 'o-', label='SCAPE-ZK (O(1))', color='#1a5490', linewidth=3)
ax.plot(B_size, s30_ver, 's--', label='Scheme [30] (O(B))', color='#e89b00')
ax.plot(B_size, ssl_ver, 'x-.', label='SSL-XIoMT (O(B))', color='#2ca02c')
ax.plot(B_size, xauth_ver, '^:', label='XAuth (O(B))', color='#c84130')
ax.set_title("Phase 4: Proof Verification Cost vs. Batch Size")
ax.set_xlabel("Batch Size / Concurrent Users (B)")
ax.set_ylabel("Time (seconds)")
format_log_axis(ax)
ax.legend()

# (3) Encryption (CP-ABE)
ax = axs[1, 0]
ax.plot(N_attr, szk_enc, 'o-', label='SCAPE-ZK', color='#1a5490', linewidth=2)
ax.plot(N_attr, ssl_enc, 'x-.', label='SSL-XIoMT', color='#2ca02c')
ax.set_title("Phase 3: Encryption (CP-ABE) Cost vs. N")
ax.set_xlabel("Number of Attributes (N)")
ax.set_ylabel("Time (seconds)")
ax.grid(True, alpha=0.3)
ax.legend()

# (4) Feature Support Matrix (Phases 2 & 5)
ax = axs[1, 1]
phases = ['Amortized Proof', 'Integrity (AggSig)', 'Delegation (PRE)']
szk_feat = np.array([111, 6, 0.55]) / 1000 
x = np.arange(len(phases))
ax.bar(x, szk_feat, width=0.4, label='SCAPE-ZK Latency (s)', color='#1a5490')
ax.set_xticks(x)
ax.set_xticklabels(phases)
ax.set_title("Phases 2 & 5: Specialized Feature Support")
ax.set_ylabel("Operation Latency (seconds)")
format_log_axis(ax)
# Force more ticks on this small range log plot
ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.4f'))
ax.legend()

OUT = Path.home() / "scape-zk" / "results" / "figures"
plt.savefig(OUT / "comprehensive_comparison_phases_seconds.png", dpi=300, bbox_inches='tight')
print(f"Comprehensive graph (seconds, formatted) saved to {OUT}")
