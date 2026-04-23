"""
Fair matched-parameter comparison figures.

Only plots baseline comparisons on workload dimensions that are genuinely
shared with SCAPE-ZK.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"
OUT.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
BLS_CSV = RESULTS / "bls_bench.csv"

REQUEST_COUNTS = [1, 10, 50, 100]
USER_COUNTS = [1, 10, 50, 100]


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


def style_axis(ax, xlabel: str, ylabel: str, title: str, xvals: list[int], y_max: float, ncol: int = 2) -> None:
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
    ax.tick_params(axis="both", labelsize=8, width=0.8)
    ax.legend(loc="upper center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, 1.03),
              handlelength=2.0, columnspacing=1.0, handletextpad=0.4)


def main() -> None:
    groth = pd.read_csv(GROTH16_CSV)
    bls = pd.read_csv(BLS_CSV)

    t_sess = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    t_req = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    scape_amort = [((t_sess + n * t_req) / n) for n in REQUEST_COUNTS]
    scape_req = [t_req for _ in REQUEST_COUNTS]

    xauth_gen = [89700.0 for _ in REQUEST_COUNTS]
    ssl_gen = [69400.0 / 10000.0 for _ in REQUEST_COUNTS]  # 6.94 ms / proof

    pair_map = {
        n: latest_value(bls, {"batch_size": n, "operation": "pairing_only"})
        for n in USER_COUNTS
    }
    scape_verify = [pair_map[n] for n in USER_COUNTS]
    xauth_verify = [9.0 * n for n in USER_COUNTS]
    ssl_verify = [(1000.0 / 918.0) * n for n in USER_COUNTS]

    colors = {
        "scape": "#1a5490",
        "scape_req": "#3a8fc2",
        "ssl": "#2ca02c",
        "xauth": "#c84130",
    }

    # Fig 1: proof cost under matched request counts
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(REQUEST_COUNTS, scape_amort, marker="o", linestyle="-", linewidth=1.8,
            markersize=4, color=colors["scape"], label="SCAPE-ZK amortized")
    ax.plot(REQUEST_COUNTS, scape_req, marker="s", linestyle="-", linewidth=1.5,
            markersize=3.7, color=colors["scape_req"], label="SCAPE-ZK request proof")
    ax.plot(REQUEST_COUNTS, xauth_gen, marker="D", linestyle="-", linewidth=1.4,
            markersize=3.5, color=colors["xauth"], label="XAuth")
    ax.plot(REQUEST_COUNTS, ssl_gen, marker="^", linestyle="-", linewidth=1.4,
            markersize=3.5, color=colors["ssl"], label="SSL-XIoMT")
    style_axis(ax, "Requests per Session / Proof Count", "Computation Time (ms)",
               "Matched-Parameter Proof Cost", REQUEST_COUNTS, max(xauth_gen) * 1.08)
    fig.savefig(OUT / "matched_proof_cost.png")
    fig.savefig(OUT / "matched_proof_cost.pdf")
    plt.close(fig)

    # Fig 2: verification scalability under matched user counts
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(USER_COUNTS, scape_verify, marker="o", linestyle="-", linewidth=1.8,
            markersize=4, color=colors["scape"], label="SCAPE-ZK on-chain")
    ax.plot(USER_COUNTS, xauth_verify, marker="D", linestyle="-", linewidth=1.4,
            markersize=3.5, color=colors["xauth"], label="XAuth")
    ax.plot(USER_COUNTS, ssl_verify, marker="^", linestyle="-", linewidth=1.4,
            markersize=3.5, color=colors["ssl"], label="SSL-XIoMT")
    style_axis(ax, "Concurrent Users / Requests", "Computation Time (ms)",
               "Matched-Parameter Verification Cost", USER_COUNTS,
               max(max(scape_verify), max(xauth_verify), max(ssl_verify)) * 1.08, ncol=3)
    fig.savefig(OUT / "matched_verification_cost.png")
    fig.savefig(OUT / "matched_verification_cost.pdf")
    plt.close(fig)

    print(f"Saved {OUT / 'matched_proof_cost.png'}")
    print(f"Saved {OUT / 'matched_verification_cost.png'}")


if __name__ == "__main__":
    main()
