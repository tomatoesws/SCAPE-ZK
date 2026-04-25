"""
Plot off-chain authorization preparation cost.

Supports either:
  1. a single-baseline comparison, or
  2. a combined chart with all modeled baselines.

This script is intentionally strict:
  - T_init is derived from the repo's measured Groth16 benchmark CSV.
  - baseline costs come from repo-known modeled anchors or a user-supplied value.
  - T_agg_overhead comes from either explicit input or a measured BLS aggregate fit.

Examples:
  python3 scripts/plot_off_chain_authorization_preparation_cost.py \
      --baseline scheme30 \
      --t-agg-source bls-aggregate-fit

  python3 scripts/plot_off_chain_authorization_preparation_cost.py \
      --all-baselines \
      --t-agg-source bls-aggregate-fit \
      --n-max 150 \
      --out-prefix off_chain_authorization_preparation_cost
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

SUMMARY_CSV = RESULTS / "cumulative_proof_modeled_summary.csv"
BLS_CSV = RESULTS / "bls_bench.csv"
GROTH16_CSV = RESULTS / "groth16_bench.csv"

KNOWN_BASELINES = {
    "scheme30": ("Scheme [30]", 20.690194),
    "ssl-xiomt": ("SSL-XIoMT", 6.94),
    "xauth": ("XAuth", 89700.0),
}

STYLE = {
    "SCAPE-ZK": {"color": "#ff7f0e", "marker": "D"},
    "XAuth": {"color": "#e41a1c", "marker": "s"},
    "SSL-XIoMT": {"color": "#1f77b4", "marker": "o"},
    "Scheme [30]": {"color": "#2ca02c", "marker": "^"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        choices=["scheme30", "ssl-xiomt", "xauth", "custom"],
        default="scheme30",
        help="Baseline curve to compare against.",
    )
    parser.add_argument(
        "--all-baselines",
        action="store_true",
        help="Plot XAuth, SSL-XIoMT, Scheme [30], and SCAPE-ZK on one chart.",
    )
    parser.add_argument(
        "--baseline-cost-ms",
        type=float,
        default=None,
        help="Required when --baseline custom.",
    )
    parser.add_argument(
        "--t-agg-overhead-ms",
        type=float,
        default=None,
        help="Exact measured preparation overhead per added item. Do not guess this.",
    )
    parser.add_argument(
        "--t-agg-source",
        choices=["manual", "bls-aggregate-fit"],
        default="bls-aggregate-fit",
        help="How to obtain T_agg_overhead_ms.",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=100,
        help="Maximum batch size on the x-axis.",
    )
    parser.add_argument(
        "--out-prefix",
        default="off_chain_authorization_preparation_cost",
        help="Output filename prefix under results/figures and results/.",
    )
    return parser.parse_args()


def latest_value(df: pd.DataFrame, filters: dict[str, object], value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def load_t_init_ms() -> float:
    groth = pd.read_csv(GROTH16_CSV)
    t_session = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    t_request = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    return t_session + t_request


def get_baseline(args: argparse.Namespace) -> tuple[str, float]:
    if args.baseline == "custom":
        if args.baseline_cost_ms is None:
            raise ValueError("--baseline-cost-ms is required when --baseline custom")
        return "Custom Baseline", float(args.baseline_cost_ms)
    return KNOWN_BASELINES[args.baseline]


def fit_bls_aggregate_slope_ms() -> tuple[float, float]:
    xs: list[float] = []
    ys: list[float] = []
    with BLS_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["operation"] == "aggregate":
                xs.append(float(row["batch_size"]))
                ys.append(float(row["mean_ms"]))
    if not xs:
        raise ValueError(f"No aggregate rows found in {BLS_CSV}")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den
    intercept = my - slope * mx
    return intercept, slope


def first_crossing(scape_y: np.ndarray, baseline_y: np.ndarray, x: np.ndarray) -> int | None:
    idx = np.where(scape_y < baseline_y)[0]
    if len(idx) == 0:
        return None
    return int(x[idx[0]])


def theoretical_crossing(t_init_ms: float, baseline_cost_ms: float, t_agg_ms: float) -> int | None:
    if baseline_cost_ms <= t_agg_ms:
        return None
    return math.floor(t_init_ms / (baseline_cost_ms - t_agg_ms)) + 1


def pick_label_points(n_max: int) -> list[int]:
    preferred = [1, 10, 20, 50, 100, 150, 200]
    pts = [n for n in preferred if n <= n_max]
    if n_max not in pts:
        pts.append(n_max)
    return pts


def pick_marker_indices(n_max: int) -> list[int]:
    return [n - 1 for n in pick_label_points(n_max)]


def main() -> None:
    args = parse_args()
    t_init_ms = load_t_init_ms()
    if args.t_agg_source == "manual":
        if args.t_agg_overhead_ms is None:
            raise ValueError("--t-agg-overhead-ms is required when --t-agg-source manual")
        t_agg_ms = float(args.t_agg_overhead_ms)
        agg_source_note = "user-supplied explicit input"
        scape_label = "SCAPE-ZK (Ours)"
    else:
        intercept_ms, t_agg_ms = fit_bls_aggregate_slope_ms()
        agg_source_note = (
            f"linear fit over results/bls_bench.csv aggregate rows; "
            f"intercept={intercept_ms:.6f} ms, slope={t_agg_ms:.6f} ms/item"
        )
        scape_label = "SCAPE-ZK (Ours)"

    x = np.arange(1, args.n_max + 1)
    scape_y = t_init_ms + (t_agg_ms * x)

    if args.all_baselines:
        baseline_specs = [
            ("XAuth [6]", KNOWN_BASELINES["xauth"][1], STYLE["XAuth"]["color"]),
            ("SSL-XIoMT [8]", KNOWN_BASELINES["ssl-xiomt"][1], STYLE["SSL-XIoMT"]["color"]),
            ("Scheme [30]", KNOWN_BASELINES["scheme30"][1], STYLE["Scheme [30]"]["color"]),
        ]
    else:
        baseline_name, baseline_cost_ms = get_baseline(args)
        color = STYLE.get(baseline_name, {"color": "#d62728"})["color"]
        baseline_specs = [(baseline_name, baseline_cost_ms, color)]

    table_dict = {
        "batch_size": x,
        "scape_off_chain_authorization_preparation_ms": scape_y,
    }
    for name, cost, _color in baseline_specs:
        safe = (
            name.lower()
            .replace(" ", "_")
            .replace("[", "")
            .replace("]", "")
            .replace("-", "_")
        )
        table_dict[f"{safe}_preparation_ms"] = cost * x
    table = pd.DataFrame(table_dict)
    table_path = RESULTS / f"{args.out_prefix}_table.csv"
    table.to_csv(table_path, index=False)

    summary_rows = [
        {
            "parameter": "T_init_ms",
            "value": round(t_init_ms, 6),
            "source": "derived: latest(session prove_fullprove) + latest(request prove_fullprove) from results/groth16_bench.csv",
        },
        {
            "parameter": "T_agg_overhead_ms",
            "value": round(t_agg_ms, 6),
            "source": agg_source_note,
        },
    ]
    crossings: dict[str, int | None] = {}
    for name, cost, _color in baseline_specs:
        baseline_y = cost * x
        cross_n = first_crossing(scape_y, baseline_y, x)
        crossings[name] = cross_n
        summary_rows.extend([
            {
                "parameter": f"{name}_baseline_cost_ms",
                "value": round(cost, 6),
                "source": "repo-known modeled anchor or explicit custom input",
            },
            {
                "parameter": f"{name}_theoretical_first_crossing_batch",
                "value": "" if theoretical_crossing(t_init_ms, cost, t_agg_ms) is None else theoretical_crossing(t_init_ms, cost, t_agg_ms),
                "source": "floor(T_init / (B - T_agg)) + 1, valid only when B > T_agg",
            },
            {
                "parameter": f"{name}_observed_first_crossing_batch",
                "value": "" if cross_n is None else cross_n,
                "source": "first integer N in plotted range where SCAPE-ZK < baseline",
            },
        ])
    summary = pd.DataFrame(summary_rows)
    summary_path = RESULTS / f"{args.out_prefix}_summary.csv"
    summary.to_csv(summary_path, index=False)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 16,
        "legend.fontsize": 9,
        "figure.dpi": 200,
    })

    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    scape_style = STYLE["SCAPE-ZK"]
    ax.plot(
        x, scape_y,
        label=scape_label,
        color=scape_style["color"],
        linewidth=2.2,
        marker=scape_style["marker"],
        markersize=6.8,
        markeredgecolor="black",
        markeredgewidth=0.6,
        markevery=pick_marker_indices(args.n_max),
    )

    all_y_max = np.max(scape_y)
    for name, cost, color in baseline_specs:
        baseline_y = cost * x
        all_y_max = max(all_y_max, np.max(baseline_y))
        style_key = name.replace(" [6]", "").replace(" [8]", "")
        marker = STYLE.get(style_key, {"marker": "o"})["marker"]
        ax.plot(
            x, baseline_y,
            label=name,
            color=color,
            linewidth=2.0,
            marker=marker,
            markersize=6.8,
            markeredgecolor="black",
            markeredgewidth=0.6,
            markevery=pick_marker_indices(args.n_max),
        )

    ax.set_title("Off-chain Authorization Preparation Cost", fontweight="bold", pad=14)
    ax.set_xlabel("Workload (Number of Requests)")
    ax.set_ylabel("Preparation Time (ms)")
    ax.set_xlim(-5, x[-1] + 5)
    if args.all_baselines:
        ax.set_yscale("log")
        ax.set_ylim(5, max(all_y_max * 2.2, 20))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _pos: f"{int(y):d}" if y >= 1 else f"{y:g}"))
    ax.set_xticks([1, 10, 20, 50, 100, 150, 200] if args.n_max >= 200 else pick_label_points(args.n_max))
    ax.grid(True, which="both", alpha=0.28)
    legend = ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=True,
        fancybox=True,
        framealpha=1.0,
        borderaxespad=0.3,
    )
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#cfcfcf")
    legend.get_frame().set_linewidth(0.8)

    png_path = FIGS / f"{args.out_prefix}.png"
    pdf_path = FIGS / f"{args.out_prefix}.pdf"
    fig.tight_layout()
    fig.savefig(png_path)
    fig.savefig(pdf_path)
    plt.close(fig)

    print(f"Saved {table_path}")
    print(f"Saved {summary_path}")
    print(f"Saved {png_path}")


if __name__ == "__main__":
    main()
