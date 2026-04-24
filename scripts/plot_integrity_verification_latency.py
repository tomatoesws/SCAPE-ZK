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
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    ax.plot(x, xauth_y, color="#e41a1c", marker="s", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="XAuth [6]")
    ax.plot(x, ssl_y, color="#1f77b4", marker="o", linewidth=2.0, markersize=6.6,
            markeredgecolor="black", markeredgewidth=0.6, label="SSL-XIoMT [8]")
    ax.plot(x, scape_y, color="#ff7f0e", marker="D", linewidth=2.2, markersize=6.8,
            markeredgecolor="black", markeredgewidth=0.6, label="SCAPE-ZK (Ours)")

    for xs, ys, color in [(x, xauth_y, "#e41a1c"), (x, ssl_y, "#1f77b4"), (x, scape_y, "#ff7f0e")]:
        for xi, yi in zip(xs, ys):
            ax.annotate(f"{yi:.3f}", (xi, yi), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8.0, color=color)

    ax.set_title("Integrity Verification Latency", fontweight="bold", pad=14)
    ax.set_xlabel("EHR File Size (MB)")
    ax.set_ylabel("Integrity Verification Time (ms)")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.28)

    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True,
                       fancybox=True, framealpha=1.0, borderaxespad=0.0)
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#cfcfcf")
    legend.get_frame().set_linewidth(0.8)

    fig.savefig(OUT / "integrity_verification_latency.png")
    fig.savefig(OUT / "integrity_verification_latency.pdf")
    plt.close(fig)

    print(f"Saved {OUT / 'integrity_verification_latency.png'}")


if __name__ == "__main__":
    main()
