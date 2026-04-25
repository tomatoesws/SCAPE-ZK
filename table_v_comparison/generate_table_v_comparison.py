#!/usr/bin/env python3
"""Generate Table V comparison graph in the house style of graph_example.

The figure is intentionally scoped to on-chain authorization verification only.
It mirrors the example chart format: serif typography, log-scale y-axis,
dense horizontal grid, in-plot legend, and the same marker/line palette.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
OUT_CSV = ROOT / "table_v_normalized_cost.csv"
OUT_SVG = ROOT / "table_v_authorization_scalability.svg"

LOADS = [1, 10, 50, 100, 200]
T_HASH = 1.0
T_GRP = 5.0
T_PAIR = 20.0
T_ZK_VERIFY = 25.0

COLORS = {
    "scape": "#2b6aa6",
    "scheme30": "#f0ad00",
    "xauth": "#c7493a",
    "ssl": "#3aa34a",
    "grid": "#9aa0a6",
    "axis": "#111111",
    "bg": "#ffffff",
    "legend_bg": "#ffffff",
    "legend_border": "#cfcfcf",
}

SCHEMES = [
    ("SCAPE-ZK", "T_pair", "Constant aggregate on-chain verification"),
    ("Scheme [30]", "T_zk_verify + T_pair + n*T_grp + n*T_hash", "Aggregate-signature verification plus linear group operations"),
    ("XAuth [6]", "n*T_hash", "Linear hash/check cost"),
    ("SSL-XIoMT [8]", "n*T_hash", "Linear hash/check cost"),
]

def onchain_cost(scheme: str, n: int) -> float:
    if scheme == "SCAPE-ZK":
        return T_PAIR
    if scheme in ["XAuth [6]", "SSL-XIoMT [8]"]:
        return n * T_HASH
    if scheme == "Scheme [30]":
        return T_ZK_VERIFY + T_PAIR + n * T_GRP + n * T_HASH
    raise ValueError(f"Unknown scheme: {scheme}")


def table_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for n in LOADS:
        for scheme, table_v_term, interpretation in SCHEMES:
            rows.append(
                {
                    "n_requests": n,
                    "scheme": scheme,
                    "table_v_onchain_term": table_v_term,
                    "interpretation": interpretation,
                    "authorization_verification_cost": onchain_cost(scheme, n),
                }
            )
    return rows


def write_csv(rows: list[dict[str, float | str]]) -> None:
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "n_requests",
                "scheme",
                "table_v_onchain_term",
                "interpretation",
                "authorization_verification_cost",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def x_pos(n: int, left: int, width: int) -> float:
    min_n = LOADS[0]
    max_n = LOADS[-1]
    return left + ((n - min_n) / (max_n - min_n)) * width


def y_pos_log(value: float, top: int, height: int, y_min: float, y_max: float) -> float:
    log_min = math.log10(y_min)
    log_max = math.log10(y_max)
    log_value = math.log10(max(value, y_min))
    frac = (log_value - log_min) / (log_max - log_min)
    return top + height - frac * height


def marker_svg(marker: str, x: float, y: float, color: str) -> str:
    stroke = "#1b1b1b"
    if marker == "circle":
        return f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="{stroke}" stroke-width="1"/>'
    if marker == "square":
        return f'  <rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{color}" stroke="{stroke}" stroke-width="1"/>'
    if marker == "triangle":
        points = f"{x:.1f},{y - 6:.1f} {x - 6:.1f},{y + 5:.1f} {x + 6:.1f},{y + 5:.1f}"
        return f'  <polygon points="{points}" fill="{color}" stroke="{stroke}" stroke-width="1"/>'
    if marker == "x":
        return (
            f'  <line x1="{x - 5:.1f}" y1="{y - 5:.1f}" x2="{x + 5:.1f}" y2="{y + 5:.1f}" '
            f'stroke="{color}" stroke-width="2"/>'
            f'\n  <line x1="{x - 5:.1f}" y1="{y + 5:.1f}" x2="{x + 5:.1f}" y2="{y - 5:.1f}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
    raise ValueError(f"Unsupported marker: {marker}")


def draw_grid(left: int, top: int, width: int, height: int, y_min: float, y_max: float) -> list[str]:
    parts: list[str] = []
    decade = int(math.floor(math.log10(y_min)))
    top_decade = int(math.ceil(math.log10(y_max)))
    for power in range(decade, top_decade + 1):
        base = 10 ** power
        for multiplier in range(1, 10):
            value = multiplier * base
            if value < y_min or value > y_max:
                continue
            y = y_pos_log(value, top, height, y_min, y_max)
            stroke_width = 0.8 if multiplier == 1 else 0.45
            opacity = 0.35 if multiplier == 1 else 0.2
            parts.append(
                f'  <line x1="{left}" y1="{y:.1f}" x2="{left + width}" y2="{y:.1f}" '
                f'stroke="{COLORS["grid"]}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
            )
    for n in LOADS:
        x = x_pos(n, left, width)
        parts.append(
            f'  <line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + height}" '
            f'stroke="{COLORS["grid"]}" stroke-width="0.55" opacity="0.25"/>'
        )
    return parts


def write_svg(rows: list[dict[str, float | str]]) -> None:
    width = 1000
    height = 680
    left = 124
    top = 72
    plot_w = 777
    plot_h = 462
    y_min = 0.8
    y_max = 1500.0

    style = {
        "SCAPE-ZK": {"color": COLORS["scape"], "dash": "", "marker": "circle", "label": "SCAPE-ZK (O(1), T_pair)"},
        "Scheme [30]": {"color": COLORS["scheme30"], "dash": "8 4", "marker": "square", "label": "Scheme [30] (O(n), agg-signature + group ops)"},
        "XAuth [6]": {"color": COLORS["xauth"], "dash": "2 4", "marker": "triangle", "label": "XAuth [6] (O(n), nT_hash)"},
        "SSL-XIoMT [8]": {"color": COLORS["ssl"], "dash": "10 4 2 4", "marker": "x", "label": "SSL-XIoMT [8] (O(n), nT_hash)"},
    }

    by_scheme: dict[str, list[dict[str, float | str]]] = {}
    for row in rows:
        by_scheme.setdefault(str(row["scheme"]), []).append(row)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'  <rect width="100%" height="100%" fill="{COLORS["bg"]}"/>',
        "  <style>",
        '    text { font-family: "Times New Roman", Times, serif; fill: #111111; }',
        "    .title { font-size: 22px; font-weight: 400; }",
        "    .axis-label { font-size: 16px; }",
        "    .tick { font-size: 12px; }",
        "    .legend { font-size: 13px; }",
        "    .note { font-size: 12px; }",
        "  </style>",
        f'  <text x="{width / 2:.1f}" y="45" text-anchor="middle" class="title">Normalized On-chain Authorization Verification Cost vs. Batch Size (n)</text>',
    ]

    parts.extend(draw_grid(left, top, plot_w, plot_h, y_min, y_max))

    parts.append(f'  <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="{COLORS["axis"]}" stroke-width="1"/>')

    for power in range(0, 4):
        value = 10 ** power
        y = y_pos_log(value, top, plot_h, y_min, y_max)
        parts.append(f'  <text x="{left - 14}" y="{y + 5:.1f}" text-anchor="end" class="tick">10^{power}</text>')

    for n in LOADS:
        x = x_pos(n, left, plot_w)
        parts.append(f'  <text x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{n}</text>')

    parts.append(
        f'  <text x="{left + plot_w / 2:.1f}" y="{top + plot_h + 55}" text-anchor="middle" class="axis-label">Batch Size / Authorization Requests (n)</text>'
    )
    parts.append(
        f'  <text x="32" y="{top + plot_h / 2:.1f}" text-anchor="middle" class="axis-label" transform="rotate(-90 32 {top + plot_h / 2:.1f})">Normalized On-chain Verification Cost</text>'
    )

    draw_order = ["SCAPE-ZK", "Scheme [30]", "XAuth [6]", "SSL-XIoMT [8]"]
    for scheme in draw_order:
        scheme_rows = by_scheme[scheme]
        points = []
        for row in scheme_rows:
            n = int(row["n_requests"])
            cost = float(row["authorization_verification_cost"])
            points.append((x_pos(n, left, plot_w), y_pos_log(cost, top, plot_h, y_min, y_max)))
        point_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        scheme_style = style[scheme]
        dash_attr = f' stroke-dasharray="{scheme_style["dash"]}"' if scheme_style["dash"] else ""
        parts.append(
            f'  <polyline points="{point_str}" fill="none" stroke="{scheme_style["color"]}" '
            f'stroke-width="2.5"{dash_attr} stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x, y in points:
            parts.append(marker_svg(str(scheme_style["marker"]), x, y, str(scheme_style["color"])))

    legend_x = left
    legend_y = top + plot_h + 85
    legend_w = plot_w
    legend_h = 45

    parts.append(
        '  <text x="480" y="95" class="note">Scheme [30] is higher than XAuth/SSL-XIoMT because it adds</text>'
    )
    parts.append(
        '  <text x="480" y="112" class="note">pairing/ZKP-related verification and linear group operations.</text>'
    )
    
    legend_rows = [
        "SCAPE-ZK",
        "Scheme [30]",
        "XAuth [6]",
        "SSL-XIoMT [8]",
    ]
    for idx, scheme in enumerate(legend_rows):
        # 2x2 layout
        lx = legend_x + (idx % 2) * (legend_w / 2)
        ly = legend_y + (idx // 2) * 22
        scheme_style = style[scheme]
        dash_attr = f' stroke-dasharray="{scheme_style["dash"]}"' if scheme_style["dash"] else ""
        parts.append(
            f'  <line x1="{lx}" y1="{ly}" x2="{lx + 32}" y2="{ly}" stroke="{scheme_style["color"]}" '
            f'stroke-width="2.5"{dash_attr} stroke-linecap="round"/>'
        )
        parts.append(marker_svg(str(scheme_style["marker"]), lx + 16, ly, str(scheme_style["color"])))
        parts.append(
            f'  <text x="{lx + 42}" y="{ly + 4}" class="legend">{escape(str(scheme_style["label"]))}</text>'
        )

    parts.append("</svg>")
    OUT_SVG.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    rows = table_rows()
    write_csv(rows)
    write_svg(rows)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
