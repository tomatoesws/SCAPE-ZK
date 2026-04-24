"""
SCAPE-ZK measured batch proof preparation latency.

This script uses only local SCAPE-ZK measurements:
  - Groth16 session + request proving from results/groth16_bench.csv
  - BLS aggregate timing slope from results/bls_bench.csv

Model used for the plotted curve:
  T_prepare(N) = T_init + slope_agg * N

where:
  - T_init = latest(session prove_fullprove) + latest(request prove_fullprove)
  - slope_agg is the least-squares slope of measured BLS aggregate timings

Outputs:
  - results/scape_batch_preparation_measured.csv
  - results/figures/scape_batch_preparation_measured.png
  - results/figures/scape_batch_preparation_measured.pdf
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
BLS_CSV = RESULTS / "bls_bench.csv"
OUT_CSV = RESULTS / "scape_batch_preparation_measured.csv"

N_MAX = 200
MARK_POINTS = [1, 10, 20, 50, 100, 150, 200]


def latest_value(df: pd.DataFrame, filters: dict, value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def fit_bls_aggregate() -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    with BLS_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["operation"] == "aggregate":
                xs.append(float(row["batch_size"]))
                ys.append(float(row["mean_ms"]))
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den
    intercept = my - slope * mx
    return intercept, slope


def main() -> None:
    groth = pd.read_csv(GROTH16_CSV)
    t_sess = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    t_req = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    t_init = t_sess + t_req

    agg_intercept, agg_slope = fit_bls_aggregate()

    xs = np.arange(1, N_MAX + 1)
    ys = t_init + agg_slope * xs

    df = pd.DataFrame({
        "batch_size": xs,
        "prepare_time_ms": ys,
        "t_init_ms": t_init,
        "agg_intercept_ms": agg_intercept,
        "agg_slope_ms_per_item": agg_slope,
    })
    df.to_csv(OUT_CSV, index=False)

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
    ax.plot(xs, ys, color="#ff7f0e", marker="D", linewidth=2.2, markersize=6.8,
            markeredgecolor="black", markeredgewidth=0.6,
            markevery=[n - 1 for n in MARK_POINTS], label="SCAPE-ZK (Measured)")
    for n in MARK_POINTS:
        y = t_init + agg_slope * n
        ax.annotate(f"{y:.3f}", (n, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8.0, color="#ff7f0e")

    ax.set_title("Batch Proof Preparation Latency", fontweight="bold", pad=14)
    ax.set_xlabel("Batch Size (N)")
    ax.set_ylabel("Preparation Time (ms)")
    ax.set_xlim(1, N_MAX)
    ax.set_xticks(MARK_POINTS)
    ax.grid(True, alpha=0.28)
    ax.legend(loc="upper left", frameon=True, fancybox=True, framealpha=1.0)

    fig.savefig(FIGS / "scape_batch_preparation_measured.png")
    fig.savefig(FIGS / "scape_batch_preparation_measured.pdf")
    plt.close(fig)

    print(f"Saved {OUT_CSV}")
    print(f"Saved {FIGS / 'scape_batch_preparation_measured.png'}")


if __name__ == "__main__":
    main()
