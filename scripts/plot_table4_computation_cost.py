"""
SCAPE-ZK Table IV computation-cost comparison plot.

This script builds a comparison figure covering the Table IV columns:
  - Proof Gen
  - Amortized Proof
  - Encrypt
  - Proof Ver
  - Integrity / Delegation

Design goals:
  1. Use measured SCAPE-ZK values from local benchmark CSVs.
  2. Use baseline anchors/simulators already present in baseline_sim.py.
  3. Never silently fabricate missing baseline values. Missing cells are
     written as NA in the summary CSV and shown as hatched placeholders in
     the figure.

Outputs:
  - results/table4_computation_cost_summary.csv
  - results/figures/table4_computation_cost.png
  - results/figures/table4_computation_cost.pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from baseline_sim import (
    load_primitives,
    scheme30_simulate,
    simulate_integrity_costs,
    sslxiomt_simulate,
    xauth_simulate,
)


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
CPABE_CSV = RESULTS / "cpabe_bench.csv"
PRE_CSV = RESULTS / "pre_bench.csv"
MERKLE_CSV = RESULTS / "merkle_bench.csv"
SUMMARY_CSV = RESULTS / "table4_computation_cost_summary.csv"

# Representative workload point for scalar Table IV comparison.
REP_ATTRS = 10
REP_REQUESTS = 50

# Optional paper-extracted overrides. Leave as None when the repo does not yet
# contain a defensible exact value for that Table IV cell.
METRICS = [
    "Proof Gen",
    "Amortized Proof",
    "Encrypt",
    "Proof Ver",
    "Integrity / Delegation",
]
SCHEMES = ["SCAPE-ZK", "XAuth", "SSL-XIoMT", "Scheme [30]"]
COLORS = {
    "SCAPE-ZK": "#1a5490",
    "XAuth": "#c84130",
    "SSL-XIoMT": "#2ca02c",
    "Scheme [30]": "#e89b00",
}


@dataclass
class ValueCell:
    value_ms: float | None
    source: str


def latest_value(df: pd.DataFrame, filters: Dict[str, object], value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def build_scape_values() -> Dict[str, ValueCell]:
    groth = pd.read_csv(GROTH16_CSV)
    cpabe = pd.read_csv(CPABE_CSV)
    pre = pd.read_csv(PRE_CSV)
    merkle = pd.read_csv(MERKLE_CSV)

    t_sess = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    t_req = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    t_req_v = latest_value(groth, {"circuit": "request", "metric": "verify"})
    t_abe = latest_value(cpabe, {"n_attrs": REP_ATTRS, "operation": "cpabe_encrypt"})
    t_sym = latest_value(cpabe, {"n_attrs": REP_ATTRS, "operation": "sym_encrypt_1KB"})
    t_pre = latest_value(pre, {"operation": "re_encrypt"})
    t_merk = latest_value(merkle, {"operation": "merkle_verify"})
    t_leaf = latest_value(merkle, {"operation": "leaf_hash"})

    return {
        "Proof Gen": ValueCell(
            t_sess + t_req,
            "derived: first-time setup proof = session prove_fullprove + request prove_fullprove",
        ),
        "Amortized Proof": ValueCell(
            (t_sess + REP_REQUESTS * t_req) / REP_REQUESTS,
            f"derived: (session + {REP_REQUESTS}*request)/{REP_REQUESTS}",
        ),
        "Encrypt": ValueCell(
            t_abe + t_sym,
            f"measured+derived: cpabe_encrypt + sym_encrypt_1KB @ N={REP_ATTRS}",
        ),
        "Proof Ver": ValueCell(t_req_v, "measured: groth16_bench.csv request verify"),
        "Integrity / Delegation": ValueCell(
            t_pre + t_merk + t_leaf,
            "derived: re_encrypt + merkle_verify + leaf_hash",
        ),
    }


def build_baseline_values() -> Dict[str, Dict[str, ValueCell]]:
    p = load_primitives()
    merkle = pd.read_csv(MERKLE_CSV)
    pre = pd.read_csv(PRE_CSV)
    t_merk = latest_value(merkle, {"operation": "merkle_verify"})
    t_leaf = latest_value(merkle, {"operation": "leaf_hash"})
    t_pre = latest_value(pre, {"operation": "re_encrypt"})
    integrity = simulate_integrity_costs(
        {
            "T_hash": p.thash_ms,
            "T_leaf_hash": t_leaf,
            "T_merk": t_merk,
            "T_pre": t_pre,
        },
        n_users=1,
        n_system_records=REP_REQUESTS,
    )
    xauth = xauth_simulate(p, n_users=1)
    ssl = sslxiomt_simulate(1, primitives=p, n_attrs=REP_ATTRS)
    scheme30 = scheme30_simulate(
        p,
        n_k_disclosed=min(REP_ATTRS, 10),
        n_attrs_total=max(REP_ATTRS, 10),
        n_issuers=5,
        batch_users=1,
    )

    return {
        "XAuth": {
            "Proof Gen": ValueCell(xauth["proof_gen_ms"], "paper anchor / baseline_sim.py"),
            "Amortized Proof": ValueCell(xauth["proof_gen_ms"], "paper anchor / baseline_sim.py"),
            "Encrypt": ValueCell(None, "NA: XAuth paper path has no directly comparable encryption cell"),
            "Proof Ver": ValueCell(xauth["verify_ms"], "paper anchor / baseline_sim.py"),
            "Integrity / Delegation": ValueCell(
                integrity["XAuth"],
                "strict integrity model / baseline_sim.py",
            ),
        },
        "SSL-XIoMT": {
            "Proof Gen": ValueCell(ssl["total_ms"], "paper anchor / baseline_sim.py"),
            "Amortized Proof": ValueCell(ssl["total_ms"], "paper anchor / baseline_sim.py"),
            "Encrypt": ValueCell(ssl["encrypt_proxy_ms"], "primitive proxy / baseline_sim.py"),
            "Proof Ver": ValueCell(ssl["verify_ms_per_proof"], "paper anchor / baseline_sim.py"),
            "Integrity / Delegation": ValueCell(
                integrity["SSL_XIoMT"],
                "strict integrity model / baseline_sim.py",
            ),
        },
        "Scheme [30]": {
            "Proof Gen": ValueCell(scheme30["issue_ms"], "primitive proxy / baseline_sim.py"),
            "Amortized Proof": ValueCell(scheme30["show_ms"], "primitive proxy / baseline_sim.py"),
            "Encrypt": ValueCell(None, "NA: Scheme [30] path is credential-oriented, not payload encryption"),
            "Proof Ver": ValueCell(scheme30["verify_ms"], "primitive proxy / baseline_sim.py"),
            "Integrity / Delegation": ValueCell(
                integrity["Scheme30"],
                "strict integrity model / baseline_sim.py",
            ),
        },
    }


def write_summary_csv(table: Dict[str, Dict[str, ValueCell]]) -> None:
    rows = []
    for scheme in SCHEMES:
        for metric in METRICS:
            cell = table[scheme][metric]
            rows.append({
                "scheme": scheme,
                "metric": metric,
                "value_ms": "" if cell.value_ms is None else round(cell.value_ms, 4),
                "source": cell.source,
            })
    pd.DataFrame(rows).to_csv(SUMMARY_CSV, index=False)


def plot_table(table: Dict[str, Dict[str, ValueCell]]) -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "figure.dpi": 180,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(11, 5.4))
    x = np.arange(len(METRICS))
    width = 0.19

    scheme_handles = []
    missing_handle = Patch(facecolor="white", edgecolor="#666666", hatch="///", label="N/A / not available")

    max_val = 1.0
    for idx, scheme in enumerate(SCHEMES):
        offsets = x + (idx - 1.5) * width
        heights = []
        for metric in METRICS:
            cell = table[scheme][metric]
            if cell.value_ms is None:
                heights.append(np.nan)
            else:
                heights.append(cell.value_ms)
                max_val = max(max_val, cell.value_ms)

        bars = ax.bar(
            offsets,
            np.nan_to_num(heights, nan=0.0),
            width=width,
            color=COLORS[scheme],
            edgecolor="black",
            linewidth=0.4,
            label=scheme,
        )
        scheme_handles.append(bars[0])

        for bar, h in zip(bars, heights):
            if np.isnan(h):
                bar.set_height(max_val * 0.012)
                bar.set_facecolor("white")
                bar.set_edgecolor("#666666")
                bar.set_hatch("///")
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    max_val * 0.018,
                    "N/A",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                    rotation=90,
                    color="#666666",
                )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.set_xticks(x)
    ax.set_xticklabels(METRICS)
    ax.set_ylabel("Computation Time (ms)")
    ax.set_title("Table IV Computation Cost Comparison")
    ax.grid(axis="y", which="major", color="#d9d9d9", linestyle="-", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        handles=scheme_handles + [missing_handle],
        labels=SCHEMES + ["N/A / not available"],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=5,
        frameon=False,
    )

    subtitle = (
        f"SCAPE-ZK uses measured local benchmarks; representative point uses N={REP_ATTRS} attrs "
        f"and n={REP_REQUESTS} requests for amortization."
    )
    fig.text(0.5, -0.02, subtitle, ha="center", va="top", fontsize=8)

    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"table4_computation_cost.{ext}")
    plt.close(fig)


def main() -> None:
    scape = build_scape_values()
    baselines = build_baseline_values()
    table: Dict[str, Dict[str, ValueCell]] = {"SCAPE-ZK": scape, **baselines}

    write_summary_csv(table)
    plot_table(table)

    print(f"Saved {SUMMARY_CSV}")
    print(f"Saved {FIGS / 'table4_computation_cost.png'}")
    print(f"Saved {FIGS / 'table4_computation_cost.pdf'}")


if __name__ == "__main__":
    main()
