"""Fig A9 — CP-ABE encrypt scales with attribute count; symmetric is negligible."""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

ROOT = Path.home() / "scape-zk"
CSV = ROOT / "results" / "cpabe_bench.csv"
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 10, "axes.labelsize": 11, "figure.dpi": 150})

df = pd.read_csv(CSV)

# Extract per-N numbers for encrypt and sym_encrypt
def get(op):
    rows = df[df["operation"] == op].sort_values("n_attrs")
    return rows["n_attrs"].tolist(), rows["mean_ms"].tolist(), rows["std_ms"].tolist()

N_abe, t_abe, s_abe = get("cpabe_encrypt")
N_sym, t_sym, s_sym = get("sym_encrypt_1KB")
N_dec, t_dec, s_dec = get("cpabe_decrypt")

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.errorbar(N_abe, t_abe, yerr=s_abe, fmt="o-", linewidth=2, markersize=8,
            color="#1a5490", capsize=4, label=r"CP-ABE encrypt  $T^{abe}_{enc}$")
ax.errorbar(N_dec, t_dec, yerr=s_dec, fmt="^--", linewidth=1.8, markersize=7,
            color="#3a8fc2", capsize=4, label="CP-ABE decrypt", alpha=0.85)
ax.errorbar(N_sym, t_sym, yerr=s_sym, fmt="s:", linewidth=1.5, markersize=6,
            color="#c84130", capsize=4, label=r"Symmetric encrypt 1 KB  $T^{sym}_{enc}$")

ax.set_xlabel("Number of policy attributes, $N$")
ax.set_ylabel("Time (ms, log scale)")
ax.set_yscale("log")
ax.set_xticks(N_abe)
ax.set_title("Fig. A9 — CP-ABE scales with attributes; symmetric is negligible")
ax.grid(True, which="both", linestyle=":", alpha=0.4)
ax.legend(loc="upper left")

# Summary annotation
ax.annotate(f"SCAPE-ZK Encrypt total at N=50:\n{t_abe[-1] + t_sym[-1]:.1f} ms",
            xy=(N_abe[-1], t_abe[-1]), xytext=(20, t_abe[-1] * 0.3),
            fontsize=9, color="#1a5490",
            arrowprops=dict(arrowstyle="->", color="black", lw=0.8))

plt.tight_layout()
for ext in ("pdf", "png"):
    plt.savefig(OUT / f"fig9_cpabe_sweep.{ext}", bbox_inches="tight")
print(f"Saved fig9_cpabe_sweep.pdf and .png")
