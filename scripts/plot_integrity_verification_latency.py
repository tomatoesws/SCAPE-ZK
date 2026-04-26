"""
Plot integrity verification latency versus EHR file size.

Uses measured data from results/integrity_filesize_bench.csv:
  - XAuth [6]: payload hash + blockchain-hash compare
  - SSL-XIoMT [8]: payload hash + commitment hash + Merkle verify
  - SCAPE-ZK: compact-leaf hash + Merkle verify

Output:
  results/figures/integrity_verification_latency.png
  results/figures/integrity_verification_latency.pdf
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path.home() / "scape-zk"
CSV = ROOT / "results" / "integrity_filesize_bench.csv"
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def latest_complete_timestamp(df: pd.DataFrame, schemes: list[str], operation: str) -> pd.Timestamp:
    rows = df[df["operation"] == operation].copy()
    if rows.empty:
        raise ValueError(f"Missing rows for operation={operation}")
    rows["_ts"] = pd.to_datetime(rows["timestamp"], utc=True)
    complete_batches = []
    for ts, batch in rows.groupby("_ts"):
        if set(schemes).issubset(set(batch["scheme"])):
            complete_batches.append(ts)
    if not complete_batches:
        raise ValueError(
            f"No complete {operation} batch found for schemes={', '.join(schemes)}"
        )
    return max(complete_batches)


def series_for_timestamp(
    df: pd.DataFrame,
    scheme: str,
    operation: str,
    timestamp: pd.Timestamp,
) -> pd.DataFrame:
    rows = df[(df["scheme"] == scheme) & (df["operation"] == operation)].copy()
    if rows.empty:
        raise ValueError(f"Missing rows for scheme={scheme}, operation={operation}")
    rows["_ts"] = pd.to_datetime(rows["timestamp"], utc=True)
    rows = rows[rows["_ts"] == timestamp].sort_values("file_size_mb")
    if rows.empty:
        raise ValueError(
            f"Missing rows for scheme={scheme}, operation={operation}, timestamp={timestamp}"
        )
    return rows


def main() -> None:
    df = pd.read_csv(CSV)
    schemes = ["xauth", "ssl_xiomt", "scape_zk"]
    batch_ts = latest_complete_timestamp(df, schemes, "total")
    xauth = series_for_timestamp(df, "xauth", "total", batch_ts)
    ssl = series_for_timestamp(df, "ssl_xiomt", "total", batch_ts)
    scape = series_for_timestamp(df, "scape_zk", "total", batch_ts)

    x = xauth["file_size_mb"].tolist()
    xauth_y = xauth["mean_ms"].tolist()
    ssl_y = ssl["mean_ms"].tolist()
    scape_y = scape["mean_ms"].tolist()

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 8.5,
        "figure.dpi": 200,
    })

    x_positions = list(range(len(x)))
    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    ax.plot(x_positions, xauth_y, color="#e41a1c", linewidth=2.0, label="XAuth [6]")
    ax.plot(x_positions, ssl_y, color="#1f77b4", linewidth=2.0, label="SSL-XIoMT [8]")
    ax.plot(x_positions, scape_y, color="#ff7f0e", linewidth=2.2, label="SCAPE-ZK (Ours)")

    ax.set_title("Integrity Verification Latency", fontweight="bold", pad=14)
    ax.set_xlabel("EHR File Size (MB)")
    ax.set_ylabel("Integrity Verification Time (ms)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([str(value) for value in x])
    ax.set_xlim(-0.25, len(x) - 0.75)
    y_max = max(max(xauth_y), max(ssl_y), max(scape_y))
    # Add visible space below the near-zero SCAPE-ZK line so it does not sit
    # directly on the bottom axis when plotted against much larger baselines.
    lower_pad = max(2.0, y_max * 0.04)
    ax.set_ylim(-lower_pad, y_max * 1.08)
    ax.grid(True, alpha=0.28)

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
    fig.savefig(OUT / "integrity_verification_latency.png")
    fig.savefig(OUT / "integrity_verification_latency.pdf")
    plt.close(fig)

    print(f"Saved {OUT / 'integrity_verification_latency.png'}")


if __name__ == "__main__":
    main()
