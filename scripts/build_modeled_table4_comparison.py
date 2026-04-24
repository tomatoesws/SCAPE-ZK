"""
Build a modeled Table IV comparison from existing local CSV benchmarks.

This script does not claim to run baseline implementations. Instead, it:
  1. reads measured SCAPE-ZK results from results/*.csv
  2. derives primitive timings from those measurements
  3. instantiates the Table IV symbolic formulas for each scheme

Outputs:
  - results/table4_modeled_comparison.csv
  - results/table4_modeled_primitives.csv
  - results/figures/table4_modeled_comparison.png
  - results/figures/table4_modeled_comparison.pdf
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path.home() / "scape-zk"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
CPABE_CSV = RESULTS / "cpabe_bench.csv"
PRE_CSV = RESULTS / "pre_bench.csv"
BLS_CSV = RESULTS / "bls_bench.csv"
MERKLE_CSV = RESULTS / "merkle_bench.csv"

MODELED_CSV = RESULTS / "table4_modeled_comparison.csv"
PRIMITIVES_CSV = RESULTS / "table4_modeled_primitives.csv"

sys.path.insert(0, str(ROOT))
from baseline_sim import (
    load_primitives,
    scheme30_simulate,
    simulate_integrity_costs,
    sslxiomt_simulate,
    xauth_simulate,
)


REP_ATTRS = 10
REP_BATCH = 50
REP_REQUESTS = 50

METRICS = [
    "Proof Gen",
    "Amortized Proof",
    "Encrypt",
    "Proof Ver",
    "Integrity / Delegation",
]
SCHEMES = ["XAuth", "SSL-XIoMT", "Scheme [30]", "SCAPE-ZK"]
COLORS = {
    "XAuth": "#c84130",
    "SSL-XIoMT": "#2ca02c",
    "Scheme [30]": "#e89b00",
    "SCAPE-ZK": "#1a5490",
}


def latest_value(df: pd.DataFrame, filters: dict, value_col: str = "mean_ms") -> float:
    rows = df.copy()
    for col, val in filters.items():
        rows = rows[rows[col] == val]
    if rows.empty:
        raise ValueError(f"Missing data for {filters}")
    rows = rows.assign(_ts=pd.to_datetime(rows["timestamp"], utc=True)).sort_values("_ts")
    return float(rows.iloc[-1][value_col])


def measure_primitives() -> dict[str, float]:
    groth = pd.read_csv(GROTH16_CSV)
    cpabe = pd.read_csv(CPABE_CSV)
    pre = pd.read_csv(PRE_CSV)
    bls = pd.read_csv(BLS_CSV)
    merkle = pd.read_csv(MERKLE_CSV)

    t_zk_prove_creq = latest_value(groth, {"circuit": "request", "metric": "prove_fullprove"})
    t_zk_prove_csess = latest_value(groth, {"circuit": "session", "metric": "prove_fullprove"})
    t_zk_verify = latest_value(groth, {"circuit": "request", "metric": "verify"})
    t_sym_enc = latest_value(cpabe, {"n_attrs": REP_ATTRS, "operation": "sym_encrypt_1KB"})
    t_abe_enc = latest_value(cpabe, {"n_attrs": REP_ATTRS, "operation": "cpabe_encrypt"})
    t_pair_group_verify = latest_value(bls, {"batch_size": REP_BATCH, "operation": "verify_agg"})
    t_hash_leaf = latest_value(merkle, {"operation": "leaf_hash"})
    t_merk_verify = latest_value(merkle, {"operation": "merkle_verify"})
    t_pre_verify = latest_value(pre, {"operation": "re_encrypt"})
    t_pair_onchain = latest_value(bls, {"batch_size": REP_BATCH, "operation": "pairing_only"})

    micro = load_primitives()

    return {
        "t_zk_prove_creq": t_zk_prove_creq,
        "t_zk_prove_csess": t_zk_prove_csess,
        "t_zk_verify": t_zk_verify,
        "t_sym_enc": t_sym_enc,
        "t_abe_enc": t_abe_enc,
        "t_ecc_enc": 0.0,
        "t_pair_group_verify": t_pair_group_verify,
        "t_hash_leaf": t_hash_leaf,
        "t_merk_verify": t_merk_verify,
        "t_pre_verify": t_pre_verify,
        "t_pair_onchain": t_pair_onchain,
        "t_hash_micro": micro.thash_ms,
        "t_grp_micro": micro.tgrp_ms,
        "t_pair_micro": micro.tpair_ms,
        "t_sym_micro": micro.tsym_ms,
        "representative_attrs": REP_ATTRS,
        "representative_batch": REP_BATCH,
        "representative_requests": REP_REQUESTS,
    }


def xauth_formula(t: dict[str, float], n: int) -> dict[str, float]:
    p = load_primitives()
    model = xauth_simulate(p, n_users=1)
    integrity = simulate_integrity_costs(
        {
            "T_hash": t["t_hash_micro"],
            "T_leaf_hash": t["t_hash_leaf"],
            "T_merk": t["t_merk_verify"],
            "T_pre": t["t_pre_verify"],
        },
        n_users=1,
        n_system_records=n,
    )
    return {
        "Proof Gen": model["proof_gen_ms"],
        "Amortized Proof": model["proof_gen_ms"],
        "Encrypt": 0.0,
        "Proof Ver": model["verify_ms"],
        "Integrity / Delegation": integrity["XAuth"],
    }


def ssl_xiomt_formula(t: dict[str, float], n: int) -> dict[str, float]:
    p = load_primitives()
    model = sslxiomt_simulate(1, primitives=p, n_attrs=REP_ATTRS)
    integrity = simulate_integrity_costs(
        {
            "T_hash": t["t_hash_micro"],
            "T_leaf_hash": t["t_hash_leaf"],
            "T_merk": t["t_merk_verify"],
            "T_pre": t["t_pre_verify"],
        },
        n_users=1,
        n_system_records=n,
    )
    return {
        "Proof Gen": model["total_ms"],
        "Amortized Proof": model["total_ms"],
        "Encrypt": model["encrypt_proxy_ms"],
        "Proof Ver": model["verify_ms_per_proof"],
        "Integrity / Delegation": integrity["SSL_XIoMT"],
    }


def scheme30_formula(t: dict[str, float], n: int) -> dict[str, float]:
    p = load_primitives()
    model = scheme30_simulate(
        p,
        n_k_disclosed=min(REP_ATTRS, 10),
        n_attrs_total=max(REP_ATTRS, 10),
        n_issuers=5,
        batch_users=max(1, n),
    )
    integrity = simulate_integrity_costs(
        {
            "T_hash": t["t_hash_micro"],
            "T_leaf_hash": t["t_hash_leaf"],
            "T_merk": t["t_merk_verify"],
            "T_pre": t["t_pre_verify"],
        },
        n_users=1,
        n_system_records=n,
    )
    return {
        "Proof Gen": model["issue_ms"],
        "Amortized Proof": model["show_ms"],
        "Encrypt": 0.0,
        "Proof Ver": model["verify_ms"],
        "Integrity / Delegation": integrity["Scheme30"],
    }


def scape_zk_formula(t: dict[str, float], n: int) -> dict[str, float]:
    return {
        "Proof Gen": t["t_zk_prove_csess"] + t["t_zk_prove_creq"],
        "Amortized Proof": (t["t_zk_prove_csess"] + n * t["t_zk_prove_creq"]) / n,
        "Encrypt": t["t_sym_enc"] + t["t_abe_enc"],
        "Proof Ver": t["t_zk_verify"],
        "Integrity / Delegation": t["t_pre_verify"] + t["t_merk_verify"] + t["t_hash_leaf"],
    }


def build_rows(primitives: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    formulas = {
        "XAuth": xauth_formula(primitives, REP_REQUESTS),
        "SSL-XIoMT": ssl_xiomt_formula(primitives, REP_REQUESTS),
        "Scheme [30]": scheme30_formula(primitives, REP_REQUESTS),
        "SCAPE-ZK": scape_zk_formula(primitives, REP_REQUESTS),
    }

    modeled_rows = []
    for scheme in SCHEMES:
        for metric in METRICS:
            modeled_rows.append({
                "scheme": scheme,
                "metric": metric,
                "value_ms": round(formulas[scheme][metric], 6),
                "mode": "modeled_comparison",
                "notes": (
                    "SCAPE-ZK uses local measured CSV values; baselines are formula-instantiated "
                    "using local primitive timings and paper anchors where available."
                ),
            })

    primitive_rows = [{"primitive": k, "value_ms": v} for k, v in primitives.items()]
    return pd.DataFrame(modeled_rows), pd.DataFrame(primitive_rows)


def plot_modeled(df: pd.DataFrame) -> None:
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

    for idx, scheme in enumerate(SCHEMES):
        sub = df[df["scheme"] == scheme]
        vals = [float(sub[sub["metric"] == metric]["value_ms"].iloc[0]) for metric in METRICS]
        ax.bar(
            x + (idx - 1.5) * width,
            vals,
            width=width,
            color=COLORS[scheme],
            edgecolor="black",
            linewidth=0.4,
            label=scheme,
        )

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(METRICS)
    ax.set_ylabel("Computation Time (ms)")
    ax.set_title("Modeled Table IV Computation Cost Comparison")
    ax.grid(axis="y", which="major", color="#d9d9d9", linestyle="-", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.11), ncol=4, frameon=False)

    fig.text(
        0.5,
        -0.02,
        (
            "Modeled comparison: SCAPE-ZK values come from local CSV benchmarks; baseline bars are "
            "formula-instantiated using the same measured primitive environment."
        ),
        ha="center",
        va="top",
        fontsize=8,
    )

    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"table4_modeled_comparison.{ext}")
    plt.close(fig)


def main() -> None:
    primitives = measure_primitives()
    modeled_df, primitive_df = build_rows(primitives)
    modeled_df.to_csv(MODELED_CSV, index=False)
    primitive_df.to_csv(PRIMITIVES_CSV, index=False)
    plot_modeled(modeled_df)

    print(f"Saved {MODELED_CSV}")
    print(f"Saved {PRIMITIVES_CSV}")
    print(f"Saved {FIGS / 'table4_modeled_comparison.png'}")
    print(f"Saved {FIGS / 'table4_modeled_comparison.pdf'}")


if __name__ == "__main__":
    main()
