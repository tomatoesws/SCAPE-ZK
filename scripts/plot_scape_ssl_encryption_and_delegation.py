"""
Generate two paper-ready comparative plots for SCAPE-ZK vs. SSL-XIoMT [8].

Figure 1: Initial encryption latency vs. attribute count
  - SCAPE-ZK: measured local hybrid encryption latency from
    `results/cpabe_bench.csv`
  - SSL-XIoMT [8]: primitive-calibrated local proxy from `baseline_sim.py`

Figure 2: Delegation latency vs. EHR file size
  - SCAPE-ZK: constant-time Hybrid PRE transformation from the latest measured
    `re_encrypt` point in `results/pre_bench.csv`
  - Traditional re-encryption baseline: linear 10 ms / MB growth

Outputs:
  - results/figures/scape_ssl_encryption_latency.png
  - results/figures/scape_ssl_encryption_latency.pdf
  - results/figures/scape_ssl_delegation_latency.png
  - results/figures/scape_ssl_delegation_latency.pdf
  - results/scape_ssl_plot_data.csv
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

CPABE_CSV = RESULTS / "cpabe_bench.csv"
PRE_CSV = RESULTS / "pre_bench.csv"
OUT_CSV = RESULTS / "scape_ssl_plot_data.csv"

ATTR_COUNTS = [5, 10, 20, 50]
TRADITIONAL_SLOPE_MS_PER_MB = 10.0

sys.path.insert(0, str(ROOT))
from baseline_sim import load_primitives, sslxiomt_simulate


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "figure.dpi": 180,
    "savefig.bbox": "tight",
})


def latest_value(df: pd.DataFrame, filters: dict[str, object], value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def measured_scape_encrypt_ms(n_attrs: int) -> float:
    cpabe = pd.read_csv(CPABE_CSV)
    t_sym = latest_value(cpabe, {"n_attrs": n_attrs, "operation": "sym_encrypt_1KB"})
    t_cpabe = latest_value(cpabe, {"n_attrs": n_attrs, "operation": "cpabe_encrypt"})
    return t_sym + t_cpabe


def modeled_ssl_encrypt_ms(n_attrs: int) -> float:
    primitives = load_primitives()
    return float(sslxiomt_simulate(1, primitives=primitives, n_attrs=n_attrs)["encrypt_proxy_ms"])


def measured_pre_reencrypt_ms() -> float:
    pre = pd.read_csv(PRE_CSV)
    rows = pre[pre["operation"] == "re_encrypt"].copy()
    if rows.empty:
        raise ValueError("Missing re_encrypt rows in pre_bench.csv")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1]["mean_ms"])


def style_axis(ax) -> None:
    ax.grid(axis="y", color="#d9d9d9", linestyle="-", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="both", labelsize=9, width=0.8)


def plot_encryption_latency(scape_vals: list[float], ssl_vals: list[float]) -> None:
    fig, ax = plt.subplots(figsize=(7.1, 4.4))
    ax.plot(
        ATTR_COUNTS,
        scape_vals,
        color="#1a5490",
        linewidth=2.2,
        marker="o",
        markersize=5,
        label="SCAPE-ZK",
    )
    ax.plot(
        ATTR_COUNTS,
        ssl_vals,
        color="#2ca02c",
        linewidth=2.0,
        linestyle="--",
        marker="s",
        markersize=4.8,
        label="SSL-XIoMT [8]",
    )

    for x, y in zip(ATTR_COUNTS, scape_vals):
        ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", color="#1a5490")
    for x, y in zip(ATTR_COUNTS, ssl_vals):
        ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, -14), ha="center", color="#2ca02c")

    ax.set_title("Initial Encryption Latency vs. Attribute Count", fontweight="semibold")
    ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("Number of Attributes")
    ax.set_xticks(ATTR_COUNTS)
    ax.set_ylim(0, max(max(scape_vals), max(ssl_vals)) * 1.18)
    ax.legend(frameon=False, loc="upper left")
    style_axis(ax)

    fig.savefig(FIGS / "scape_ssl_encryption_latency.png")
    fig.savefig(FIGS / "scape_ssl_encryption_latency.pdf")
    plt.close(fig)


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
        color="#d62728",
        linewidth=2.2,
        marker="s",
        markersize=7.0,
        markeredgecolor="black",
        markeredgewidth=0.7,
        label="Traditional Re-encryption",
    )

    for x in plot_sizes_mb:
        ax.annotate(
            f"{pre_benchmark_ms:.4f}",
            (x, pre_benchmark_ms),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            color="#ff7f0e",
        )
        y = x * TRADITIONAL_SLOPE_MS_PER_MB
        ax.annotate(
            f"{y:.0f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            color="#d62728",
        )

    ax.set_title("Delegation Latency", fontweight="bold", fontsize=18, pad=16)
    ax.set_xlabel("EHR File Size (MB)")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(plot_sizes_mb)
    ax.set_xlim(1, 200)
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

    fig.savefig(FIGS / "scape_ssl_delegation_latency.png")
    fig.savefig(FIGS / "scape_ssl_delegation_latency.pdf")
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
    scape_vals = [measured_scape_encrypt_ms(n) for n in ATTR_COUNTS]
    ssl_vals = [modeled_ssl_encrypt_ms(n) for n in ATTR_COUNTS]
    pre_benchmark_ms = measured_pre_reencrypt_ms()

    plot_encryption_latency(scape_vals, ssl_vals)
    delegation_df = plot_delegation_latency(pre_benchmark_ms)

    enc_rows = []
    for n, y in zip(ATTR_COUNTS, scape_vals):
        enc_rows.append({
            "figure": "encryption_latency",
            "scheme": "SCAPE-ZK",
            "x_value": n,
            "x_unit": "attributes",
            "latency_ms": round(y, 6),
            "basis": "measured_cpabe_csv",
            "notes": "Local benchmark from cpabe_bench.csv: sym_encrypt_1KB + cpabe_encrypt.",
        })
    for n, y in zip(ATTR_COUNTS, ssl_vals):
        enc_rows.append({
            "figure": "encryption_latency",
            "scheme": "SSL-XIoMT [8]",
            "x_value": n,
            "x_unit": "attributes",
            "latency_ms": round(y, 6),
            "basis": "primitive_calibrated_model",
            "notes": "baseline_sim.py formula instantiated with local primitive timings for the SSL-XIoMT encryption path.",
        })
    enc_rows = pd.DataFrame(enc_rows)

    pd.concat([enc_rows, delegation_df], ignore_index=True).to_csv(OUT_CSV, index=False)

    print("SCAPE-ZK encryption latency curve :", ", ".join(f"{n}attr={y:.6f} ms" for n, y in zip(ATTR_COUNTS, scape_vals)))
    print("SSL-XIoMT encryption latency curve:", ", ".join(f"{n}attr={y:.6f} ms" for n, y in zip(ATTR_COUNTS, ssl_vals)))
    print(f"SCAPE-ZK PRE re_encrypt constant: {pre_benchmark_ms:.6f} ms")
    print(f"Saved data table to {OUT_CSV}")
    print(f"Saved figures to {FIGS}")


if __name__ == "__main__":
    main()
