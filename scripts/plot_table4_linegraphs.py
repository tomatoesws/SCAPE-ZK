"""
Table IV / cost-comparison line graphs for SCAPE-ZK.

Styled to resemble a paper figure: serif fonts, top legend, thin lines,
horizontal guide lines, and linear y-axes with explicit ticks.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"
OUT.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
CPABE_CSV = RESULTS / "cpabe_bench.csv"
BLS_CSV = RESULTS / "bls_bench.csv"

ATTR_COUNTS = [5, 10, 20, 50]
BATCH_SIZES = [1, 10, 50, 100, 200]


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "legend.fontsize": 8,
    "figure.dpi": 180,
    "savefig.bbox": "tight",
})


def latest_value(df: pd.DataFrame, filters: dict, value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def scape_proof_generation() -> list[float]:
    df = pd.read_csv(GROTH16_CSV)
    circuit_for_attrs = {
        5: "session_5",
        10: "session",
        20: "session_20",
        50: "session_50",
    }
    return [
        latest_value(df, {"circuit": circuit_for_attrs[n], "metric": "prove_fullprove"})
        for n in ATTR_COUNTS
    ]


def scape_amortized_curve() -> tuple[list[int], list[float]]:
    df = pd.read_csv(GROTH16_CSV)
    t_sess = latest_value(df, {"circuit": "session", "metric": "prove_fullprove"})
    t_req = latest_value(df, {"circuit": "request", "metric": "prove_fullprove"})
    n_vals = [1, 5, 10, 25, 50, 100, 200]
    amortized = [((t_sess + n * t_req) / n) for n in n_vals]
    return n_vals, amortized


def scape_encrypt_curve() -> list[float]:
    df = pd.read_csv(CPABE_CSV)
    values = []
    for n in ATTR_COUNTS:
        abe = latest_value(df, {"n_attrs": n, "operation": "cpabe_encrypt"})
        sym = latest_value(df, {"n_attrs": n, "operation": "sym_encrypt_1KB"})
        values.append(abe + sym)
    return values


def scape_verification_curve() -> list[float]:
    df = pd.read_csv(BLS_CSV)
    return [
        latest_value(df, {"batch_size": b, "operation": "pairing_only"})
        for b in BATCH_SIZES
    ]


def main() -> None:
    szk_gen = scape_proof_generation()
    n_amort, szk_amort = scape_amortized_curve()
    szk_enc = scape_encrypt_curve()
    szk_ver = scape_verification_curve()

    # Baseline curves carried over from the repo's existing analysis.
    xauth_gen = [89700.0] * len(ATTR_COUNTS)
    ssl_gen = [7.6] * len(ATTR_COUNTS)
    scheme30_gen = [25.0, 35.0, 45.0, 65.0]

    xauth_amort = [89700.0] * len(n_amort)
    ssl_amort = [7.6] * len(n_amort)
    scheme30_amort = [25.0 + 20.0 / max(1, n) for n in n_amort]

    ssl_enc = [10.0, 18.0, 30.0, 80.0]

    xauth_ver = [9.0 * b for b in BATCH_SIZES]
    ssl_ver = [1.089 * b for b in BATCH_SIZES]
    scheme30_ver = [latest_value(pd.read_csv(BLS_CSV), {"batch_size": b, "operation": "verify_agg"})
                    for b in BATCH_SIZES]

    colors = {
        "scape": "#1a5490",
        "scheme30": "#e89b00",
        "ssl": "#2ca02c",
        "xauth": "#c84130",
    }

    fig, axs = plt.subplots(2, 2, figsize=(13, 9))
    plt.subplots_adjust(hspace=0.34, wspace=0.28)

    def style_axis(ax, xlabel: str, ylabel: str, title: str, xvals: list[int], y_max: float) -> None:
        ax.set_title(title, fontweight="semibold", pad=8)
        ax.set_xlabel(xlabel, fontweight="semibold")
        ax.set_ylabel(ylabel, fontweight="semibold")
        ax.set_xticks(xvals)
        ax.set_ylim(0, y_max)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
        ax.grid(axis="y", color="#d9d9d9", linestyle="-", linewidth=0.8)
        ax.grid(axis="x", visible=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)
        ax.tick_params(axis="both", labelsize=8, width=0.8)
        ax.legend(loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.02),
                  handlelength=2.0, columnspacing=0.9, handletextpad=0.4)

    def add_zoom_inset(ax, xvals, series, labels, colors_map, markers_map,
                       xlim=None, ylim=None, width="44%", height="44%", loc="center right"):
        ins = inset_axes(ax, width=width, height=height, loc=loc, borderpad=1.2)
        for y, label in zip(series, labels):
            ins.plot(
                xvals, y,
                marker=markers_map[label], linestyle="-",
                color=colors_map[label], linewidth=1.1, markersize=2.8
            )
        if xlim is not None:
            ins.set_xlim(*xlim)
        if ylim is not None:
            ins.set_ylim(*ylim)
        ins.grid(axis="y", color="#e0e0e0", linestyle="-", linewidth=0.6)
        ins.grid(axis="x", visible=False)
        ins.tick_params(axis="both", labelsize=6, width=0.6, pad=1)
        for spine in ins.spines.values():
            spine.set_linewidth(0.6)
        ins.set_title("Zoom", fontsize=6.5, pad=2)
        return ins

    marker_map = {
        "SCAPE-ZK": "o",
        "Scheme [30]": "s",
        "SSL-XIoMT": "^",
        "XAuth": "D",
    }
    color_map = {
        "SCAPE-ZK": colors["scape"],
        "Scheme [30]": colors["scheme30"],
        "SSL-XIoMT": colors["ssl"],
        "XAuth": colors["xauth"],
    }

    # 1. Proof generation
    ax = axs[0, 0]
    ax.plot(ATTR_COUNTS, szk_gen, marker=marker_map["SCAPE-ZK"], linestyle="-", color=color_map["SCAPE-ZK"], linewidth=1.6, markersize=4, label="SCAPE-ZK")
    ax.plot(ATTR_COUNTS, scheme30_gen, marker=marker_map["Scheme [30]"], linestyle="-", color=color_map["Scheme [30]"], linewidth=1.4, markersize=3.5, label="Scheme [30]")
    ax.plot(ATTR_COUNTS, ssl_gen, marker=marker_map["SSL-XIoMT"], linestyle="-", color=color_map["SSL-XIoMT"], linewidth=1.4, markersize=3.5, label="SSL-XIoMT")
    ax.plot(ATTR_COUNTS, xauth_gen, marker=marker_map["XAuth"], linestyle="-", color=color_map["XAuth"], linewidth=1.4, markersize=3.5, label="XAuth")
    style_axis(ax, "Number of Attributes", "Computation Time (ms)", "Proof Generation Time",
               ATTR_COUNTS, y_max=max(xauth_gen) * 1.08)
    add_zoom_inset(
        ax,
        ATTR_COUNTS,
        [szk_gen, scheme30_gen, ssl_gen],
        ["SCAPE-ZK", "Scheme [30]", "SSL-XIoMT"],
        color_map,
        marker_map,
        xlim=(4, 51),
        ylim=(0, max(szk_gen) * 1.12),
    )

    # 2. Amortized proof
    ax = axs[0, 1]
    ax.plot(n_amort, szk_amort, marker=marker_map["SCAPE-ZK"], linestyle="-", color=color_map["SCAPE-ZK"], linewidth=1.6, markersize=4, label="SCAPE-ZK")
    ax.plot(n_amort, scheme30_amort, marker=marker_map["Scheme [30]"], linestyle="-", color=color_map["Scheme [30]"], linewidth=1.4, markersize=3.5, label="Scheme [30]")
    ax.plot(n_amort, ssl_amort, marker=marker_map["SSL-XIoMT"], linestyle="-", color=color_map["SSL-XIoMT"], linewidth=1.4, markersize=3.5, label="SSL-XIoMT")
    ax.plot(n_amort, xauth_amort, marker=marker_map["XAuth"], linestyle="-", color=color_map["XAuth"], linewidth=1.4, markersize=3.5, label="XAuth")
    style_axis(ax, "Requests per Session", "Per-Request Time (ms)", "Amortized Proof Time",
               n_amort, y_max=max(xauth_amort) * 1.08)
    add_zoom_inset(
        ax,
        n_amort,
        [szk_amort, scheme30_amort, ssl_amort],
        ["SCAPE-ZK", "Scheme [30]", "SSL-XIoMT"],
        color_map,
        marker_map,
        xlim=(1, 200),
        ylim=(0, max(szk_amort) * 1.15),
    )

    # 3. Encryption
    ax = axs[1, 0]
    ax.plot(ATTR_COUNTS, szk_enc, marker="o", linestyle="-", color=colors["scape"], linewidth=1.6, markersize=4, label="SCAPE-ZK")
    ax.plot(ATTR_COUNTS, ssl_enc, marker="^", linestyle="-", color=colors["ssl"], linewidth=1.4, markersize=3.5, label="SSL-XIoMT")
    style_axis(ax, "Number of Attributes", "Computation Time (ms)", "Encryption Time",
               ATTR_COUNTS, y_max=max(max(szk_enc), max(ssl_enc)) * 1.12)
    ax.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.02),
              handlelength=2.0, columnspacing=0.9, handletextpad=0.4)

    # 4. Verification scalability
    ax = axs[1, 1]
    ax.plot(BATCH_SIZES, szk_ver, marker="o", linestyle="-", color=colors["scape"], linewidth=1.6, markersize=4, label="SCAPE-ZK")
    ax.plot(BATCH_SIZES, scheme30_ver, marker="s", linestyle="-", color=colors["scheme30"], linewidth=1.4, markersize=3.5, label="Scheme [30]")
    ax.plot(BATCH_SIZES, ssl_ver, marker="^", linestyle="-", color=colors["ssl"], linewidth=1.4, markersize=3.5, label="SSL-XIoMT")
    ax.plot(BATCH_SIZES, xauth_ver, marker="D", linestyle="-", color=colors["xauth"], linewidth=1.4, markersize=3.5, label="XAuth")
    style_axis(ax, "Batch Size", "Computation Time (ms)", "Proof Verification Time",
               BATCH_SIZES, y_max=max(max(scheme30_ver), max(xauth_ver)) * 1.08)

    fig.suptitle("Table IV Focused Line Graphs for SCAPE-ZK Comparison", fontsize=11, fontweight="semibold", y=0.98)

    for ext in ("png", "pdf"):
        plt.savefig(OUT / f"table4_linegraphs_paperstyle.{ext}")

    print(f"Saved {OUT / 'table4_linegraphs_paperstyle.png'}")
    print(f"Saved {OUT / 'table4_linegraphs_paperstyle.pdf'}")


if __name__ == "__main__":
    main()
