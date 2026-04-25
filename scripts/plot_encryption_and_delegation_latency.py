"""
Generate the report's delegation-latency figure.

Figure: Delegation latency vs. EHR file size
  - SCAPE-ZK: constant-time Hybrid PRE transformation from the latest measured
    `re_encrypt` point in `results/pre_bench.csv`
  - Traditional re-encryption baseline: linear 10 ms / MB growth

Outputs:
  - results/figures/delegation_latency.png
  - results/figures/delegation_latency.pdf
  - results/encryption_and_delegation_latency_data.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

PRE_CSV = RESULTS / "pre_bench.csv"
OUT_CSV = RESULTS / "encryption_and_delegation_latency_data.csv"

TRADITIONAL_SLOPE_MS_PER_MB = 10.0


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "figure.dpi": 180,
    "savefig.bbox": "tight",
})


def measured_pre_reencrypt_ms() -> float:
    pre = pd.read_csv(PRE_CSV)
    rows = pre[pre["operation"] == "re_encrypt"].copy()
    if rows.empty:
        raise ValueError("Missing re_encrypt rows in pre_bench.csv")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1]["mean_ms"])


def plot_delegation_latency(pre_benchmark_ms: float) -> pd.DataFrame:
    plot_sizes_mb = np.array([1, 10, 20, 50, 100, 150, 200], dtype=int)
    file_sizes_mb = np.arange(1, 201, 1)
    scape_ms = np.full_like(plot_sizes_mb, pre_benchmark_ms, dtype=float)
    traditional_ms = plot_sizes_mb.astype(float) * TRADITIONAL_SLOPE_MS_PER_MB

    fig, ax = plt.subplots(figsize=(11.8, 6.2))
    ax.plot(
        plot_sizes_mb,
        scape_ms,
        color="#ff7f0e",
        linewidth=2.2,
        marker="D",
        markersize=7.2,
        markeredgecolor="black",
        markeredgewidth=0.7,
        label="SCAPE-ZK (Ours)",
    )
    ax.plot(
        plot_sizes_mb,
        traditional_ms,
        color="#7b3fb3",
        linewidth=2.2,
        marker="*",
        markersize=7.0,
        markeredgecolor="black",
        markeredgewidth=0.7,
        label="Traditional Re-encryption",
    )

    ax.set_title("Delegation Latency", fontweight="bold", fontsize=18, pad=16)
    ax.set_xlabel("EHR File Size (MB)")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(plot_sizes_mb)
    ax.set_xlim(-5, 205)
    ax.set_yscale("log")
    ax.set_ylim(pre_benchmark_ms * 0.45, traditional_ms.max() * 2.2)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, _: f"{y:.4f}" if y < 1 else f"{y:.0f}")
    )
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=True,
        fancybox=True,
        framealpha=0.95,
        edgecolor="#cccccc",
    )
    ax.grid(True, which="both", color="#bfbfbf", alpha=0.35, linewidth=0.8)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    ax.tick_params(axis="both", labelsize=11, width=0.9)
    fig.subplots_adjust(right=0.78, top=0.88)

    fig.savefig(FIGS / "delegation_latency.png")
    fig.savefig(FIGS / "delegation_latency.pdf")
    plt.close(fig)

    rows = []
    dense_scape_ms = np.full_like(file_sizes_mb, pre_benchmark_ms, dtype=float)
    dense_traditional_ms = file_sizes_mb.astype(float) * TRADITIONAL_SLOPE_MS_PER_MB

    for x, y in zip(file_sizes_mb, dense_scape_ms):
        rows.append({
            "figure": "delegation_latency",
            "scheme": "SCAPE-ZK",
            "x_value": int(x),
            "x_unit": "MB",
            "latency_ms": round(float(y), 6),
            "basis": "measured_pre_csv",
            "notes": "Hybrid PRE transforms only CT_k, so latency is payload-size independent; constant uses latest measured re_encrypt mean.",
        })
    for x, y in zip(file_sizes_mb, dense_traditional_ms):
        rows.append({
            "figure": "delegation_latency",
            "scheme": "Traditional Re-encryption",
            "x_value": int(x),
            "x_unit": "MB",
            "latency_ms": round(float(y), 6),
            "basis": "user_linear_model",
            "notes": "Owner must download, decrypt, and re-encrypt the full payload: 10 ms per MB.",
        })
    return pd.DataFrame(rows)


def main() -> None:
    pre_benchmark_ms = measured_pre_reencrypt_ms()

    delegation_df = plot_delegation_latency(pre_benchmark_ms)
    delegation_df.to_csv(OUT_CSV, index=False)

    print(f"SCAPE-ZK PRE re_encrypt constant: {pre_benchmark_ms:.6f} ms")
    print(f"Saved data table to {OUT_CSV}")
    print(f"Saved figures to {FIGS}")


if __name__ == "__main__":
    main()
