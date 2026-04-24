"""
Modeled cumulative proof-generation comparison.

This script intentionally mixes:
  - measured SCAPE-ZK proof timings from local CSV benchmarks
  - baseline figures/proxies from baseline_sim.py

Outputs:
  - results/cumulative_proof_modeled_table.csv
  - results/cumulative_proof_modeled_summary.csv
  - results/figures/cumulative_proof_modeled.png
  - results/figures/cumulative_proof_modeled.pdf
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
TABLE_CSV = RESULTS / "cumulative_proof_modeled_table.csv"
SUMMARY_CSV = RESULTS / "cumulative_proof_modeled_summary.csv"
FIG_PNG = FIGS / "cumulative_proof_modeled.png"
FIG_PDF = FIGS / "cumulative_proof_modeled.pdf"

sys.path.insert(0, str(ROOT))
from baseline_sim import load_primitives, scheme30_simulate, sslxiomt_simulate, xauth_simulate


REQUESTS = list(range(1, 51))
REP_ATTRS = 10

COLORS = {
    "SCAPE-ZK": "#1a5490",
    "XAuth": "#c84130",
    "SSL-XIoMT": "#2ca02c",
    "Scheme [30]": "#e89b00",
}


def latest_value(df: pd.DataFrame, filters: dict, value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def first_crossing(scape_vals: list[float], baseline_vals: list[float]) -> int | None:
    for idx, (scape, base) in enumerate(zip(scape_vals, baseline_vals), start=1):
        if scape < base:
            return idx
    return None


def main() -> None:
    groth = pd.read_csv(GROTH16_CSV)
    primitives = load_primitives()

    # SCAPE-ZK local measured values.
    session_ms = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    request_ms = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    scape_initial_first_request_ms = session_ms + request_ms

    # Baseline modeled/proxied values.
    xauth_per_request_ms = xauth_simulate(primitives, n_users=1)["proof_gen_ms"]
    ssl_per_request_ms = sslxiomt_simulate(1, primitives=primitives, n_attrs=REP_ATTRS)["total_ms"]
    scheme30_per_request_ms = scheme30_simulate(
        primitives,
        n_k_disclosed=min(REP_ATTRS, 10),
        n_attrs_total=max(REP_ATTRS, 10),
        n_issuers=5,
        batch_users=1,
    )["show_ms"]

    scape_cumulative = [scape_initial_first_request_ms + request_ms * (n - 1) for n in REQUESTS]
    xauth_cumulative = [xauth_per_request_ms * n for n in REQUESTS]
    ssl_cumulative = [ssl_per_request_ms * n for n in REQUESTS]
    scheme30_cumulative = [scheme30_per_request_ms * n for n in REQUESTS]

    table = pd.DataFrame({
        "requests_in_session": REQUESTS,
        "scape_cumulative_ms": scape_cumulative,
        "scape_avg_per_request_ms": [v / n for n, v in zip(REQUESTS, scape_cumulative)],
        "xauth_cumulative_ms": xauth_cumulative,
        "ssl_xiomt_cumulative_ms": ssl_cumulative,
        "scheme30_cumulative_ms": scheme30_cumulative,
    })
    table.to_csv(TABLE_CSV, index=False)

    crossings = {
        "XAuth": first_crossing(scape_cumulative, xauth_cumulative),
        "SSL-XIoMT": first_crossing(scape_cumulative, ssl_cumulative),
        "Scheme [30]": first_crossing(scape_cumulative, scheme30_cumulative),
    }

    universal_window_start = None
    for n, scape, xauth, ssl, s30 in zip(
        REQUESTS, scape_cumulative, xauth_cumulative, ssl_cumulative, scheme30_cumulative
    ):
        if scape < xauth and scape < ssl and scape < s30:
            universal_window_start = n
            break

    summary = pd.DataFrame([
        {
            "scheme": "SCAPE-ZK",
            "role": "first_request_total",
            "value_ms": round(scape_initial_first_request_ms, 6),
            "source": "local measured: session prove_fullprove + request prove_fullprove",
        },
        {
            "scheme": "SCAPE-ZK",
            "role": "subsequent_request_cost",
            "value_ms": round(request_ms, 6),
            "source": "local measured: request prove_fullprove",
        },
        {
            "scheme": "XAuth",
            "role": "baseline_per_request_cost",
            "value_ms": round(xauth_per_request_ms, 6),
            "source": "baseline_sim.py paper anchor",
        },
        {
            "scheme": "SSL-XIoMT",
            "role": "baseline_per_request_cost",
            "value_ms": round(ssl_per_request_ms, 6),
            "source": "baseline_sim.py paper anchor / proxy mix",
        },
        {
            "scheme": "Scheme [30]",
            "role": "baseline_per_request_cost",
            "value_ms": round(scheme30_per_request_ms, 6),
            "source": "baseline_sim.py primitive proxy (show_ms)",
        },
        {
            "scheme": "XAuth",
            "role": "crossing_request_index",
            "value_ms": "" if crossings["XAuth"] is None else crossings["XAuth"],
            "source": "first n where SCAPE cumulative < baseline cumulative",
        },
        {
            "scheme": "SSL-XIoMT",
            "role": "crossing_request_index",
            "value_ms": "" if crossings["SSL-XIoMT"] is None else crossings["SSL-XIoMT"],
            "source": "first n where SCAPE cumulative < baseline cumulative",
        },
        {
            "scheme": "Scheme [30]",
            "role": "crossing_request_index",
            "value_ms": "" if crossings["Scheme [30]"] is None else crossings["Scheme [30]"],
            "source": "first n where SCAPE cumulative < baseline cumulative",
        },
        {
            "scheme": "ALL_BASELINES",
            "role": "universal_efficiency_window_start",
            "value_ms": "" if universal_window_start is None else universal_window_start,
            "source": "first n where SCAPE is below all modeled baselines",
        },
    ])
    summary.to_csv(SUMMARY_CSV, index=False)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "legend.fontsize": 9,
        "figure.dpi": 200,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.plot(REQUESTS, scape_cumulative, color=COLORS["SCAPE-ZK"], linewidth=2.2, label="SCAPE-ZK (measured)")
    ax.plot(REQUESTS, xauth_cumulative, color=COLORS["XAuth"], linewidth=1.8, label="XAuth (modeled)")
    ax.plot(REQUESTS, ssl_cumulative, color=COLORS["SSL-XIoMT"], linewidth=1.8, label="SSL-XIoMT (modeled)")
    ax.plot(REQUESTS, scheme30_cumulative, color=COLORS["Scheme [30]"], linewidth=1.8, label="Scheme [30] (modeled)")

    if universal_window_start is not None:
        ax.axvspan(universal_window_start, REQUESTS[-1], color=COLORS["SCAPE-ZK"], alpha=0.10)
        ax.text(
            (universal_window_start + REQUESTS[-1]) / 2,
            ax.get_ylim()[1] * 0.85,
            "SCAPE-ZK Efficiency Window",
            color=COLORS["SCAPE-ZK"],
            ha="center",
            va="center",
            fontsize=9,
        )

    for scheme, x_cross in crossings.items():
        if x_cross is None:
            continue
        y_vals = {
            "XAuth": xauth_cumulative,
            "SSL-XIoMT": ssl_cumulative,
            "Scheme [30]": scheme30_cumulative,
        }[scheme]
        ax.scatter([x_cross], [scape_cumulative[x_cross - 1]], color="black", s=18, zorder=5)
        ax.annotate(
            f"{scheme} cross @ {x_cross}",
            xy=(x_cross, scape_cumulative[x_cross - 1]),
            xytext=(x_cross + 1.2, scape_cumulative[x_cross - 1] * 1.08),
            fontsize=8,
            arrowprops={"arrowstyle": "->", "lw": 0.8},
        )

    if universal_window_start is None:
        ax.text(
            0.98,
            0.06,
            "No universal efficiency window under current modeled baselines",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#888888", "alpha": 0.9},
        )

    ax.set_title("Modeled Cumulative Proof Generation Time")
    ax.set_xlabel("Number of Consecutive Requests in a Session")
    ax.set_ylabel("Cumulative Execution Time (ms)")
    ax.set_xlim(1, REQUESTS[-1])
    ax.set_yscale("log")
    ax.grid(True, alpha=0.28)
    ax.legend(loc="upper left", frameon=True)

    note = (
        "SCAPE-ZK line uses local measured Groth16 timings; baselines use baseline_sim.py "
        "anchors/proxies. Scheme [30] uses modeled per-request show_ms."
    )
    fig.text(0.5, -0.03, note, ha="center", fontsize=8)

    fig.savefig(FIG_PNG)
    fig.savefig(FIG_PDF)
    plt.close(fig)

    print(f"Saved {TABLE_CSV}")
    print(f"Saved {SUMMARY_CSV}")
    print(f"Saved {FIG_PNG}")


if __name__ == "__main__":
    main()
