"""
SCAPE-ZK Figure A8 — Session prove time vs. number of attributes.
Demonstrates graceful scaling and constant verify cost.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path.home() / "scape-zk"
CSV = ROOT / "results" / "groth16_bench.csv"
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 11,
    "legend.fontsize": 9, "figure.dpi": 150, "savefig.bbox": "tight",
})

# Map circuit name -> (N_attrs, measured_constraints)
SWEEP = {
    "session_5":  (5,  10588),
    "session":    (10, 11705),    # baseline from Day 2 (circuit=session)
    "session_20": (20, 14436),
    "session_50": (50, 22404),
}

df = pd.read_csv(CSV)

def pooled(circuit, metric, col="mean_ms"):
    rows = df[(df["circuit"] == circuit) & (df["metric"] == metric)]
    if len(rows) == 0: return None, None
    total_n = rows["n"].sum()
    mean = (rows[col] * rows["n"]).sum() / total_n
    if total_n <= len(rows):
        std = rows["std_ms"].mean()
    else:
        var = ((rows["n"] - 1) * rows["std_ms"]**2).sum() / (total_n - len(rows))
        std = var ** 0.5
    return mean, std

# Collect pooled data for each sweep point
points = []
for circ, (n_attr, constraints) in SWEEP.items():
    prove_mean, prove_std = pooled(circ, "prove_fullprove")
    verify_mean, verify_std = pooled(circ, "verify")
    if prove_mean is None:
        print(f"WARN: no data for {circ}")
        continue
    points.append({
        "circuit": circ, "n_attr": n_attr, "constraints": constraints,
        "prove_mean": prove_mean, "prove_std": prove_std,
        "verify_mean": verify_mean, "verify_std": verify_std,
    })

points.sort(key=lambda p: p["n_attr"])

print("\nAttribute sweep data:")
print(f"{'N':>4} {'|C|':>8} {'Prove (ms)':>14} {'Verify (ms)':>14}")
for p in points:
    print(f"{p['n_attr']:>4} {p['constraints']:>8} "
          f"{p['prove_mean']:>8.1f} ± {p['prove_std']:>4.1f} "
          f"{p['verify_mean']:>8.2f} ± {p['verify_std']:>4.2f}")

N = [p["n_attr"] for p in points]
C = [p["constraints"] for p in points]
P = [p["prove_mean"] for p in points]
Ps = [p["prove_std"] for p in points]
V = [p["verify_mean"] for p in points]
Vs = [p["verify_std"] for p in points]

# =============================================================
# FIG A8 — Dual panel: prove scales, verify doesn't
# =============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# LEFT: prove time vs N_attr with dual x-axis (constraints)
color_prove = "#1a5490"
ax1.errorbar(N, P, yerr=Ps, fmt="o-", color=color_prove, linewidth=2.2,
             markersize=9, capsize=4, markerfacecolor=color_prove,
             markeredgecolor="black", label="Measured")

# Linear-fit reference
coef = np.polyfit(N, P, 1)
N_fine = np.linspace(min(N), max(N), 50)
ax1.plot(N_fine, np.polyval(coef, N_fine), "--", color="#888",
         linewidth=1, alpha=0.6,
         label=f"Linear fit: {coef[0]:.1f}·N + {coef[1]:.0f}")

for p in points:
    ax1.annotate(f"|C|={p['constraints']:,}", xy=(p["n_attr"], p["prove_mean"]),
                 xytext=(p["n_attr"] + 1, p["prove_mean"] - 35),
                 fontsize=8, color="#444")

ax1.set_xlabel("Number of attributes, $N$")
ax1.set_ylabel("Session proof generation time (ms)")
ax1.set_title("(a) Prove time scales gracefully with attribute count")
ax1.grid(True, linestyle=":", alpha=0.4)
ax1.legend(loc="upper left")
ax1.set_xticks(N)

# RIGHT: verify time (should be flat)
color_verify = "#3a8fc2"
ax2.errorbar(N, V, yerr=Vs, fmt="s-", color=color_verify, linewidth=2.2,
             markersize=9, capsize=4, markerfacecolor=color_verify,
             markeredgecolor="black", label="Measured")

# Mean reference line
v_mean = np.mean(V)
ax2.axhline(v_mean, linestyle=":", color="#888", linewidth=1,
            label=f"Mean: {v_mean:.1f} ms")

ax2.set_xlabel("Number of attributes, $N$")
ax2.set_ylabel("Verification time (ms)")
ax2.set_title("(b) Verify is $\\mathcal{O}(1)$ — independent of $N$")
ax2.grid(True, linestyle=":", alpha=0.4)
ax2.legend(loc="upper right")
ax2.set_xticks(N)
ax2.set_ylim(0, max(V) * 1.4)

fig.suptitle("Fig. A8 — SCAPE-ZK Session circuit scaling under attribute count sweep",
             fontsize=11, y=1.02)
plt.tight_layout()

for ext in ("pdf", "png"):
    plt.savefig(OUT / f"fig8_attribute_sweep.{ext}")

print(f"\nSaved: {OUT / 'fig8_attribute_sweep.pdf'}")
print(f"Saved: {OUT / 'fig8_attribute_sweep.png'}")
