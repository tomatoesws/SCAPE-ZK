#!/usr/bin/env python3
"""
Generate the proof-verification latency figure.

Comparison scope:
- SCAPE-ZK: real measured Groth16 request-proof verification from
  results/groth16_bench.csv.
- Scheme [26]: Table IV reconstruction from SCAPE_ZK.pdf:
  T_zk^v + O(T_pair + n*T_grp), instantiated conservatively as
  T_zk^v + T_pair + n*T_grp using measured primitives from
  results/primitive_microbench.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"
OUT.mkdir(parents=True, exist_ok=True)

GROTH16_CSV = RESULTS / "groth16_bench.csv"
PRIMITIVES_CSV = RESULTS / "primitive_microbench.csv"
DATA_CSV = RESULTS / "proof_verification_latency_data.csv"

REQUESTS = [1, 10, 50, 100, 200, 500]

COLORS = {
    "SCAPE-ZK (Ours)": "#ff8c00",
    "Scheme [26]": "#2ca02c",
}
def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def latest_metric(path: Path, filters: dict[str, str], value_col: str = "mean_ms") -> float:
    rows = read_rows(path)
    matches = [
        row for row in rows
        if all(row.get(key) == value for key, value in filters.items())
    ]
    if not matches:
        raise ValueError(f"Missing rows in {path} for {filters}")
    return float(max(matches, key=lambda row: row["timestamp"])[value_col])


def primitive_values() -> dict[str, float]:
    values: dict[str, float] = {}
    for row in read_rows(PRIMITIVES_CSV):
        primitive = row["primitive"]
        mean_ms = float(row["mean_ms"])
        if primitive.startswith("Tpair "):
            values["Tpair"] = mean_ms
        elif primitive.startswith("Tgrp "):
            values["Tgrp"] = mean_ms
    missing = sorted({"Tpair", "Tgrp"} - values.keys())
    if missing:
        raise ValueError(f"Missing primitive measurements: {', '.join(missing)}")
    return values


def write_source_table(rows: list[dict[str, Any]]) -> None:
    with DATA_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["scheme", "concurrent_requests", "latency_ms", "basis"],
        )
        writer.writeheader()
        writer.writerows(rows)


def plot() -> None:
    t_zk_verify = latest_metric(
        GROTH16_CSV,
        {"circuit": "request", "metric": "verify"},
    )
    prim = primitive_values()
    t_pair = prim["Tpair"]
    t_grp = prim["Tgrp"]

    scape_values = [t_zk_verify for _ in REQUESTS]
    scheme26_values = [
        t_zk_verify + t_pair + (n * t_grp)
        for n in REQUESTS
    ]

    series = [
        (
            "SCAPE-ZK (Ours)",
            scape_values,
            "T_zk^v; latest request verify mean from results/groth16_bench.csv",
        ),
        (
            "Scheme [26]",
            scheme26_values,
            "T_zk^v + T_pair + n*T_grp; Table IV in SCAPE_ZK.pdf, primitives from results/primitive_microbench.csv",
        ),
    ]

    source_rows: list[dict[str, Any]] = []
    for label, values, basis in series:
        for n, value in zip(REQUESTS, values):
            source_rows.append({
                "scheme": label,
                "concurrent_requests": n,
                "latency_ms": round(value, 6),
                "basis": basis,
            })
    write_source_table(source_rows)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 8.5,
        "figure.dpi": 180,
        "savefig.bbox": "tight",
    })

    x_positions = list(range(len(REQUESTS)))
    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    for label, values, _basis in series:
        ax.plot(
            x_positions,
            values,
            label=label,
            color=COLORS[label],
            linewidth=2.5,
        )

    ax.set_title("Proof Verification Latency", fontweight="bold", pad=18)
    ax.set_xlabel("Concurrent Verification Requests")
    ax.set_ylabel("Verification Latency (ms)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(request) for request in REQUESTS])
    ax.set_xlim(-0.25, len(REQUESTS) - 0.75)
    ax.grid(True, which="both", linestyle="-", alpha=0.28, linewidth=0.8)
    ax.tick_params(axis="both", width=0.9)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=len(labels),
        frameon=False,
        columnspacing=1.25,
        handlelength=2.6,
    )
    fig.tight_layout()
    fig.savefig(OUT / "proof_verification_latency.png")
    fig.savefig(OUT / "proof_verification_latency.pdf")
    plt.close(fig)

    print(f"SCAPE-ZK T_zk^v: {t_zk_verify:.6f} ms")
    print(f"Scheme [26] T_pair: {t_pair:.6f} ms")
    print(f"Scheme [26] T_grp: {t_grp:.6f} ms")
    print(f"Saved {OUT / 'proof_verification_latency.png'}")
    print(f"Saved {OUT / 'proof_verification_latency.pdf'}")
    print(f"Wrote {DATA_CSV}")


if __name__ == "__main__":
    plot()
