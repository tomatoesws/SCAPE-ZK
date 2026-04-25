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


def latest_series(df: pd.DataFrame, scheme: str, operation: str) -> pd.DataFrame:
    rows = df[(df["scheme"] == scheme) & (df["operation"] == operation)].copy()
    if rows.empty:
        raise ValueError(f"Missing rows for scheme={scheme}, operation={operation}")
    rows["_ts"] = pd.to_datetime(rows["timestamp"], utc=True)
    latest_ts = rows["_ts"].max()
    rows = rows[rows["_ts"] == latest_ts].sort_values("file_size_mb")
    return rows


def main() -> None:
    df = pd.read_csv(CSV)
    xauth = latest_series(df, "xauth", "total")
    ssl = latest_series(df, "ssl_xiomt", "total")
    scape = latest_series(df, "scape_zk", "total")

    x = xauth["file_size_mb"].tolist()
    xauth_y = xauth["mean_ms"].tolist()
    ssl_y = ssl["mean_ms"].tolist()
    scape_y = scape["mean_ms"].tolist()

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 16,
        "legend.fontsize": 9,
        "figure.dpi": 200,
    })

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.plot(x, xauth_y, color="#e41a1c", marker="s", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="XAuth [6]")
    ax.plot(x, ssl_y, color="#1f77b4", marker="o", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="SSL-XIoMT [8]")
    ax.plot(x, scape_y, color="#ff7f0e", marker="D", linewidth=2.2, markersize=6.8,
            markeredgecolor="black", markeredgewidth=0.6, label="SCAPE-ZK (Ours)")

    ax.set_title("Integrity Verification Latency", fontweight="bold", pad=14)
    ax.set_xlabel("EHR File Size (MB)")
    ax.set_ylabel("Integrity Verification Time (ms)")
    ax.set_xticks(x)
    ax.set_xlim(min(x) - 3, max(x) + 3)
    y_max = max(max(xauth_y), max(ssl_y), max(scape_y))
    # Add visible space below the near-zero SCAPE-ZK line so it does not sit
    # directly on the bottom axis when plotted against much larger baselines.
    lower_pad = max(2.0, y_max * 0.04)
    ax.set_ylim(-lower_pad, y_max * 1.08)
    ax.grid(True, alpha=0.28)

    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True,
                       fancybox=True, framealpha=1.0, borderaxespad=0.0)
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#cfcfcf")
    legend.get_frame().set_linewidth(0.8)

    fig.subplots_adjust(left=0.14, right=0.80, top=0.88, bottom=0.16)
    fig.savefig(OUT / "integrity_verification_latency.png", bbox_inches=None)
    fig.savefig(OUT / "integrity_verification_latency.pdf", bbox_inches=None)
    plt.close(fig)

    print(f"Saved {OUT / 'integrity_verification_latency.png'}")


if __name__ == "__main__":
    main()
