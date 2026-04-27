#!/usr/bin/env python3
"""Generate Section 7.C/7.D figures from repeated SCAPE-ZK Caliper results."""

from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_CSV = ROOT / "caliper-operations-repeated-summary.csv"
FIGURES_DIR = ROOT / "figures"

COLORS = {
    "teal": "#007C89",
    "coral": "#D95F43",
    "navy": "#2F455C",
    "gold": "#C4932F",
    "green": "#4C8B56",
    "gray": "#5F6670",
    "grid": "#D8DDE3",
    "text": "#222831",
    "muted": "#66707A",
    "bg": "#FFFFFF",
}

OP_LABELS = {
    "register": "Register",
    "verifyproof": "VerifyProof",
    "revoke": "Revoke",
    "updatecred": "UpdateCred",
    "recordexists": "RecordExists",
}
OP_ORDER = ["register", "verifyproof", "revoke", "updatecred", "recordexists"]
LOADS = [100, 500, 1000]


def read_rows() -> list[dict[str, str]]:
    with SUMMARY_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_name(name: str) -> tuple[str, int]:
    op, load = name.rsplit("-", 1)
    return op, int(load.removesuffix("tx"))


def fmt(value: float) -> str:
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def write_svg(path: Path, body: str, width: int, height: int) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <rect width="100%" height="100%" fill="{COLORS['bg']}"/>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; fill: {COLORS['text']}; }}
    .title {{ font-size: 22px; font-weight: 700; }}
    .subtitle {{ font-size: 13px; fill: {COLORS['muted']}; }}
    .axis {{ font-size: 12px; fill: {COLORS['muted']}; }}
    .label {{ font-size: 12px; fill: {COLORS['text']}; }}
    .value {{ font-size: 12px; font-weight: 700; fill: {COLORS['text']}; }}
    .legend {{ font-size: 12px; fill: {COLORS['text']}; }}
    .grid {{ stroke: {COLORS['grid']}; stroke-width: 1; }}
    .axis-line {{ stroke: #9AA3AD; stroke-width: 1; }}
    .error {{ stroke: {COLORS['text']}; stroke-width: 1.5; }}
  </style>
{body}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def axis_parts(
    title: str,
    subtitle: str,
    y_label: str,
    y_max: float,
    width: int,
    height: int,
    margin_left: int,
    margin_right: int,
    margin_top: int,
    margin_bottom: int,
) -> tuple[list[str], int, int]:
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    parts = [
        f'  <text x="{margin_left}" y="38" class="title">{escape(title)}</text>',
        f'  <text x="{margin_left}" y="60" class="subtitle">{escape(subtitle)}</text>',
        f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">{escape(y_label)}</text>',
    ]
    for i in range(6):
        value = y_max * i / 5
        y = margin_top + plot_h - (value / y_max) * plot_h
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(value)}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')
    return parts, plot_w, plot_h


def draw_error_bar_chart(
    path: Path,
    title: str,
    subtitle: str,
    items: list[tuple[str, float, float]],
    y_label: str,
    color: str,
    width: int = 940,
    height: int = 570,
) -> None:
    margin_left = 90
    margin_right = 45
    margin_top = 92
    margin_bottom = 98
    y_max = max(mean + sd for _, mean, sd in items) * 1.18
    parts, plot_w, plot_h = axis_parts(
        title, subtitle, y_label, y_max, width, height, margin_left, margin_right, margin_top, margin_bottom
    )
    bar_gap = 28
    bar_w = (plot_w - bar_gap * (len(items) + 1)) / len(items)

    for idx, (name, mean, sd) in enumerate(items):
        x = margin_left + bar_gap + idx * (bar_w + bar_gap)
        bar_h = (mean / y_max) * plot_h
        y = margin_top + plot_h - bar_h
        cx = x + bar_w / 2
        err_top = margin_top + plot_h - ((mean + sd) / y_max) * plot_h
        err_bottom = margin_top + plot_h - (max(mean - sd, 0) / y_max) * plot_h
        parts.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{color}"/>')
        parts.append(f'  <line x1="{cx:.1f}" y1="{err_top:.1f}" x2="{cx:.1f}" y2="{err_bottom:.1f}" class="error"/>')
        parts.append(f'  <line x1="{cx - 8:.1f}" y1="{err_top:.1f}" x2="{cx + 8:.1f}" y2="{err_top:.1f}" class="error"/>')
        parts.append(f'  <line x1="{cx - 8:.1f}" y1="{err_bottom:.1f}" x2="{cx + 8:.1f}" y2="{err_bottom:.1f}" class="error"/>')
        parts.append(f'  <text x="{cx:.1f}" y="{err_top - 8:.1f}" text-anchor="middle" class="value">{fmt(mean)}</text>')
        parts.append(f'  <text x="{cx:.1f}" y="{margin_top + plot_h + 24}" text-anchor="middle" class="label">{escape(name)}</text>')

    parts.append(f'  <text x="{margin_left}" y="{height - 24}" class="legend">Error bars show sample SD across 10 logged Caliper trials.</text>')
    write_svg(path, "\n".join(parts), width, height)


def draw_throughput_by_load(rows: dict[tuple[str, int], dict[str, float]]) -> None:
    width = 990
    height = 590
    margin_left = 90
    margin_right = 45
    margin_top = 95
    margin_bottom = 105
    y_max = max(rows[(op, load)]["throughput_tps_mean"] for op in OP_ORDER for load in LOADS) * 1.18
    parts, plot_w, plot_h = axis_parts(
        "SCAPE-ZK Throughput Scaling by Operation",
        "Hyperledger Fabric 4-peer network; means across 10 Caliper trials",
        "Throughput (TPS)",
        y_max,
        width,
        height,
        margin_left,
        margin_right,
        margin_top,
        margin_bottom,
    )
    colors = [COLORS["teal"], COLORS["coral"], COLORS["navy"], COLORS["gold"], COLORS["green"]]
    group_gap = 62
    group_w = (plot_w - group_gap * (len(LOADS) + 1)) / len(LOADS)
    inner_gap = 8
    bar_w = (group_w - inner_gap * (len(OP_ORDER) - 1)) / len(OP_ORDER)

    for load_idx, load in enumerate(LOADS):
        group_x = margin_left + group_gap + load_idx * (group_w + group_gap)
        for op_idx, op in enumerate(OP_ORDER):
            mean = rows[(op, load)]["throughput_tps_mean"]
            x = group_x + op_idx * (bar_w + inner_gap)
            bar_h = (mean / y_max) * plot_h
            y = margin_top + plot_h - bar_h
            parts.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{colors[op_idx]}"/>')
        parts.append(f'  <text x="{group_x + group_w / 2:.1f}" y="{margin_top + plot_h + 26}" text-anchor="middle" class="label">{load} tx</text>')

    legend_y = height - 30
    for idx, op in enumerate(OP_ORDER):
        x = margin_left + idx * 155
        parts.append(f'  <rect x="{x}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{colors[idx]}"/>')
        parts.append(f'  <text x="{x + 20}" y="{legend_y}" class="legend">{OP_LABELS[op]}</text>')

    write_svg(FIGURES_DIR / "repeated-throughput-by-load.svg", "\n".join(parts), width, height)


def draw_failure_summary(rows: dict[tuple[str, int], dict[str, float]]) -> None:
    items = []
    for op in OP_ORDER:
        success = sum(rows[(op, load)]["succ_total"] for load in LOADS)
        fail = sum(rows[(op, load)]["fail_total"] for load in LOADS)
        items.append((OP_LABELS[op], success, fail))

    width = 920
    height = 460
    margin_left = 90
    margin_right = 45
    margin_top = 88
    margin_bottom = 88
    y_max = max(success + fail for _, success, fail in items) * 1.12
    parts, plot_w, plot_h = axis_parts(
        "SCAPE-ZK Transaction Success Across Repeated Trials",
        "All operation/load combinations completed with zero failed transactions",
        "Transactions",
        y_max,
        width,
        height,
        margin_left,
        margin_right,
        margin_top,
        margin_bottom,
    )
    gap = 30
    bar_w = (plot_w - gap * (len(items) + 1)) / len(items)
    for idx, (name, success, fail) in enumerate(items):
        x = margin_left + gap + idx * (bar_w + gap)
        bar_h = (success / y_max) * plot_h
        y = margin_top + plot_h - bar_h
        parts.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{COLORS["green"]}"/>')
        parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="value">{int(success):,}</text>')
        parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{margin_top + plot_h + 24}" text-anchor="middle" class="label">{escape(name)}</text>')
        if fail:
            parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{y + 18:.1f}" text-anchor="middle" class="value">{int(fail)} failed</text>')
    parts.append(f'  <text x="{margin_left}" y="{height - 24}" class="legend">Each operation totals 15,000 successful transactions: 100, 500, and 1000 tx rounds over 10 trials.</text>')
    write_svg(FIGURES_DIR / "repeated-success-summary.svg", "\n".join(parts), width, height)


def main() -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    parsed: dict[tuple[str, int], dict[str, float]] = {}
    for row in read_rows():
        op, load = split_name(row["name"])
        parsed[(op, load)] = {
            "succ_total": float(row["succ_total"]),
            "fail_total": float(row["fail_total"]),
            "avg_latency_s_mean": float(row["avg_latency_s_mean"]),
            "avg_latency_s_sd": float(row["avg_latency_s_sd"]),
            "throughput_tps_mean": float(row["throughput_tps_mean"]),
            "throughput_tps_sd": float(row["throughput_tps_sd"]),
        }

    tx1000 = [(OP_LABELS[op], parsed[(op, 1000)]["throughput_tps_mean"], parsed[(op, 1000)]["throughput_tps_sd"]) for op in OP_ORDER]
    draw_error_bar_chart(
        FIGURES_DIR / "repeated-throughput-1000tx.svg",
        "SCAPE-ZK Operation Throughput at 1000 Transactions",
        "Hyperledger Fabric 4-peer network; n=10 Caliper trials",
        tx1000,
        "Throughput (TPS)",
        COLORS["teal"],
    )

    latency1000 = [(OP_LABELS[op], parsed[(op, 1000)]["avg_latency_s_mean"] * 1000, parsed[(op, 1000)]["avg_latency_s_sd"] * 1000) for op in OP_ORDER]
    draw_error_bar_chart(
        FIGURES_DIR / "repeated-latency-1000tx.svg",
        "SCAPE-ZK Operation Latency at 1000 Transactions",
        "Hyperledger Fabric 4-peer network; n=10 Caliper trials",
        latency1000,
        "Average latency (ms)",
        COLORS["coral"],
    )

    draw_throughput_by_load(parsed)
    draw_failure_summary(parsed)
    print(f"Generated {len(list(FIGURES_DIR.glob('*.svg')))} SVG figures in {FIGURES_DIR}")


if __name__ == "__main__":
    main()
