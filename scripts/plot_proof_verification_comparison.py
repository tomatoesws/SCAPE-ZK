"""
Generate the report's proof-verification latency figure.
"""

import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import ScalarFormatter

B = [1, 10, 50, 100, 200]

# Paper-style plotted values for the verification comparison figure.
scape_zk_v = [13.293, 13.293, 13.293, 13.293, 13.293]
scheme_30_v = [30.843951, 30.863886, 30.952486, 31.063236, 31.284736]
xauth_v = [9.0, 90.0, 450.0, 900.0, 1800.0]
ssl_xiomt_v = [1.089325, 10.893246, 54.466231, 108.932462, 217.864924]

COLORS = {
    "xauth": "#e41a1c",
    "ssl": "#1f77b4",
    "scheme30": "#2ca02c",
    "scape": "#ff8c00",
}

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 12,
    "axes.labelsize": 18,
    "axes.titlesize": 20,
    "legend.fontsize": 13,
    "figure.dpi": 180,
})

fig, ax = plt.subplots(figsize=(14, 7))

series = [
    ("XAuth [6]", xauth_v, COLORS["xauth"], "s"),
    ("SSL-XIoMT [8]", ssl_xiomt_v, COLORS["ssl"], "o"),
    ("Scheme [30]", scheme_30_v, COLORS["scheme30"], "^"),
    ("SCAPE-ZK (Ours)", scape_zk_v, COLORS["scape"], "D"),
]

for label, values, color, marker in series:
    ax.plot(
        B,
        values,
        label=label,
        color=color,
        marker=marker,
        linewidth=2.4,
        markersize=9.5,
        markeredgecolor="black",
        markeredgewidth=0.6,
    )

ax.set_title("Proof Verification Latency", fontweight="bold", pad=18)
ax.set_xlabel("Batch Size", fontweight="bold")
ax.set_ylabel("Execution Time (ms)", fontweight="bold")
ax.set_yscale('log')
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.yaxis.set_minor_formatter(plt.NullFormatter())
ax.set_xticks(B)
ax.set_xlim(-18, 212)
ax.set_ylim(0.75, 2600)
ax.grid(True, which="both", linestyle="-", alpha=0.28, linewidth=0.8)
ax.tick_params(axis="both", labelsize=15, width=0.9)
ax.tick_params(axis="x", pad=10)
ax.legend(
    loc="upper left",
    bbox_to_anchor=(1.04, 1.02),
    frameon=True,
    fancybox=True,
    framealpha=1.0,
)
fig.subplots_adjust(left=0.12, right=0.78, top=0.88, bottom=0.15)
fig.savefig(OUT / "proof_verification_latency.png")
fig.savefig(OUT / "proof_verification_latency.pdf")
plt.close(fig)

print(f"Saved {OUT / 'proof_verification_latency.png'}")
print(f"Saved {OUT / 'proof_verification_latency.pdf'}")
