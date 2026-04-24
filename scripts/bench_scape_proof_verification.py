"""
SCAPE-ZK measured proof verification latency.

This script uses only local SCAPE-ZK verification measurements from
results/bls_bench.csv and plots:
  - pairing_only: on-chain O(1) pairing path
  - verify_agg: measured aggregate verification path
  - verify_naive: measured naive batch verification path

Outputs:
  - results/scape_proof_verification_measured.csv
  - results/figures/scape_proof_verification_measured.png
  - results/figures/scape_proof_verification_measured.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

BLS_CSV = RESULTS / "bls_bench.csv"
OUT_CSV = RESULTS / "scape_proof_verification_measured.csv"


def latest_series(df: pd.DataFrame, operation: str) -> pd.DataFrame:
    rows = df[df["operation"] == operation].copy()
    if rows.empty:
        raise ValueError(f"Missing rows for operation={operation}")
    rows["_ts"] = pd.to_datetime(rows["timestamp"], utc=True)
    latest_ts = rows["_ts"].max()
    rows = rows[rows["_ts"] == latest_ts].sort_values("batch_size")
    return rows


def main() -> None:
    df = pd.read_csv(BLS_CSV)
    pair = latest_series(df, "pairing_only")
    agg = latest_series(df, "verify_agg")
    naive = latest_series(df, "verify_naive")

    out = pd.DataFrame({
        "batch_size": pair["batch_size"],
        "pairing_only_ms": pair["mean_ms"],
        "verify_agg_ms": agg["mean_ms"],
        "verify_naive_ms": naive["mean_ms"],
    })
    out.to_csv(OUT_CSV, index=False)

    x = pair["batch_size"].tolist()
    pair_y = pair["mean_ms"].tolist()
    agg_y = agg["mean_ms"].tolist()
    naive_y = naive["mean_ms"].tolist()

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 16,
        "legend.fontsize": 9,
        "figure.dpi": 200,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.plot(x, pair_y, color="#ff7f0e", marker="D", linewidth=2.2, markersize=6.8,
            markeredgecolor="black", markeredgewidth=0.6, label="SCAPE-ZK On-chain O(1)")
    ax.plot(x, agg_y, color="#1f77b4", marker="o", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="Aggregate Verify")
    ax.plot(x, naive_y, color="#2ca02c", marker="^", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="Naive Verify")

    for xs, ys, color in [(x, pair_y, "#ff7f0e"), (x, agg_y, "#1f77b4"), (x, naive_y, "#2ca02c")]:
        for xi, yi in zip(xs, ys):
            ax.annotate(f"{yi:.3f}", (xi, yi), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8.0, color=color)

    ax.set_title("Proof Verification Latency", fontweight="bold", pad=14)
    ax.set_xlabel("Batch Size")
    ax.set_ylabel("Verification Time (ms)")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.28)

    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True,
                       fancybox=True, framealpha=1.0, borderaxespad=0.0)
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#cfcfcf")
    legend.get_frame().set_linewidth(0.8)

    fig.savefig(FIGS / "scape_proof_verification_measured.png")
    fig.savefig(FIGS / "scape_proof_verification_measured.pdf")
    plt.close(fig)

    print(f"Saved {OUT_CSV}")
    print(f"Saved {FIGS / 'scape_proof_verification_measured.png'}")


if __name__ == "__main__":
    main()
