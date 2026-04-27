#!/usr/bin/env python3
"""Generate Table V comparison graph in the house style of graph_example.

The figure is intentionally scoped to on-chain authorization verification only.
It mirrors the example chart format: serif typography, log-scale y-axis,
dense horizontal grid, categorical x-axis spacing, and the same line palette.

The costs are primitive-calibrated milliseconds. They are not full protocol
reimplementations of the baselines; they instantiate the Table V formulas with
locally measured primitive timings.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT.parent / "results"
PRIMITIVE_CSV = RESULTS / "primitive_microbench.csv"
GROTH16_CSV = RESULTS / "groth16_bench.csv"
OUT_CSV = ROOT / "table_v_primitive_calibrated_cost.csv"
OUT_SVG = ROOT / "table_v_authorization_scalability.svg"

LOADS = [1, 10, 50, 100, 200, 1000, 5000, 10000, 20000, 50000]
IIOT_SSI_NAME = (
    "Cross-Domain Identity Authentication Scheme for the IIoT Identification "
    "Resolution System Based on Self-Sovereign Identity [30]"
)
IIOT_SSI_LABEL = "IIoT SSI Identity Resolution [30]"

COLORS = {
    "scape": "#e5a800",
    "scheme30": "#2ca02c",
    "xauth": "#c94a3b",
    "ssl": "#1f5f9f",
    "grid": "#9aa0a6",
    "axis": "#111111",
    "bg": "#ffffff",
    "legend_bg": "#ffffff",
    "legend_border": "#cfcfcf",
}

SCHEMES = [
    ("SCAPE-ZK", "T_pair", "Constant aggregate on-chain verification", "formula_derived"),
    (IIOT_SSI_NAME, "T_zk_verify + T_pair + n*T_grp + n*T_hash", "Aggregate-signature verification plus linear group operations", "formula_derived"),
    ("XAuth [6]", "n*T_hash", "Linear hash/check cost", "formula_derived"),
    ("SSL-XIoMT [8]", "n*T_hash", "Linear hash/check cost", "formula_derived"),
]


def latest_matching_value(path: Path, filters: dict[str, str], value_col: str = "mean_ms") -> float:
    matches: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if all(row.get(key) == value for key, value in filters.items()):
                matches.append(row)
    if not matches:
        raise ValueError(f"No rows in {path} match {filters}")
    matches.sort(key=lambda row: row.get("timestamp", ""))
    return float(matches[-1][value_col])


def primitive_value(name: str) -> float:
    with PRIMITIVE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [row for row in reader if row["primitive"] == name]
    if not rows:
        raise ValueError(f"No primitive row named {name!r} in {PRIMITIVE_CSV}")
    rows.sort(key=lambda row: row.get("timestamp", ""))
    return float(rows[-1]["mean_ms"])


def measured_terms() -> dict[str, float]:
    return {
        "T_hash_ms": primitive_value("Thash (SHA-256, 32B input)"),
        "T_grp_ms": primitive_value("Tgrp (BLS12-381 G1 scalar multiplication)"),
        "T_pair_ms": primitive_value("Tpair (BLS12-381 bilinear pairing)"),
        "T_zk_verify_ms": latest_matching_value(
            GROTH16_CSV,
            {"circuit": "request", "metric": "verify"},
        ),
    }


def onchain_cost(scheme: str, n: int, terms: dict[str, float]) -> float:
    if scheme == "SCAPE-ZK":
        return terms["T_pair_ms"]
    if scheme in ["XAuth [6]", "SSL-XIoMT [8]"]:
        return n * terms["T_hash_ms"]
    if scheme == IIOT_SSI_NAME:
        return (
            terms["T_zk_verify_ms"]
            + terms["T_pair_ms"]
            + n * terms["T_grp_ms"]
            + n * terms["T_hash_ms"]
        )
    raise ValueError(f"Unknown scheme: {scheme}")


def table_rows() -> list[dict[str, float | str]]:
    terms = measured_terms()
    rows: list[dict[str, float | str]] = []
    for n in LOADS:
        for scheme, table_v_term, interpretation, basis in SCHEMES:
            rows.append(
                {
                    "n_requests": n,
                    "scheme": scheme,
                    "table_v_onchain_term": table_v_term,
                    "interpretation": interpretation,
                    "basis": basis,
                    "authorization_verification_cost_ms": onchain_cost(scheme, n, terms),
                    "T_hash_ms": terms["T_hash_ms"],
                    "T_grp_ms": terms["T_grp_ms"],
                    "T_pair_ms": terms["T_pair_ms"],
                    "T_zk_verify_ms": terms["T_zk_verify_ms"],
                    "source_file": "results/primitive_microbench.csv; results/groth16_bench.csv",
                    "source_filter_or_formula": table_v_term,
                    "notes": "Table V on-chain authorization-verification formula instantiated with local primitive measurements; not an end-to-end baseline runtime.",
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
                "basis",
                "authorization_verification_cost_ms",
                "T_hash_ms",
                "T_grp_ms",
                "T_pair_ms",
                "T_zk_verify_ms",
                "source_file",
                "source_filter_or_formula",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def x_pos(n: int, left: int, width: int) -> float:
    x_indices = {load: idx for idx, load in enumerate(LOADS)}
    return left + (x_indices[n] / (len(LOADS) - 1)) * width


def y_pos_log(value: float, top: int, height: int, y_min: float, y_max: float) -> float:
    log_min = math.log10(y_min)
    log_max = math.log10(y_max)
    log_value = math.log10(max(value, y_min))
    frac = (log_value - log_min) / (log_max - log_min)
    return top + height - frac * height


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
    width = 1120
    height = 680
    left = 124
    top = 72
    plot_w = 690
    plot_h = 462
    y_min = 0.001
    y_max = 30000.0

    style = {
        "SCAPE-ZK": {"color": COLORS["scape"], "dash": "", "label": "SCAPE-ZK (Ours)"},
        IIOT_SSI_NAME: {"color": COLORS["scheme30"], "dash": "8 4", "label": IIOT_SSI_LABEL},
        "XAuth [6]": {"color": COLORS["xauth"], "dash": "10 4 2 4", "label": "XAuth [6]"},
        "SSL-XIoMT [8]": {"color": COLORS["ssl"], "dash": "2 4", "label": "SSL-XIoMT [8]"},
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
        f'  <text x="{width / 2:.1f}" y="45" text-anchor="middle" class="title">On-chain Authorization Verification Cost</text>',
    ]

    parts.extend(draw_grid(left, top, plot_w, plot_h, y_min, y_max))

    parts.append(f'  <rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="{COLORS["axis"]}" stroke-width="1"/>')

    for power in range(-3, 3):
        value = 10 ** power
        if value < y_min or value > y_max:
            continue
        y = y_pos_log(value, top, plot_h, y_min, y_max)
        label = f"{value:g}"
        parts.append(f'  <text x="{left - 14}" y="{y + 5:.1f}" text-anchor="end" class="tick">{label}</text>')

    for n in LOADS:
        x = x_pos(n, left, plot_w)
        parts.append(f'  <text x="{x:.1f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{n}</text>')

    parts.append(
        f'  <text x="{left + plot_w / 2:.1f}" y="{top + plot_h + 55}" text-anchor="middle" class="axis-label">Workload (Number of requests)</text>'
    )
    parts.append(
        f'  <text x="32" y="{top + plot_h / 2:.1f}" text-anchor="middle" class="axis-label" transform="rotate(-90 32 {top + plot_h / 2:.1f})">Verification cost (ms)</text>'
    )

    draw_order = ["SCAPE-ZK", IIOT_SSI_NAME, "XAuth [6]", "SSL-XIoMT [8]"]
    for scheme in draw_order:
        scheme_rows = by_scheme[scheme]
        points = []
        for row in scheme_rows:
            n = int(row["n_requests"])
            cost = float(row["authorization_verification_cost_ms"])
            points.append((x_pos(n, left, plot_w), y_pos_log(cost, top, plot_h, y_min, y_max)))
        point_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        scheme_style = style[scheme]
        dash_attr = f' stroke-dasharray="{scheme_style["dash"]}"' if scheme_style["dash"] else ""
        parts.append(
            f'  <polyline points="{point_str}" fill="none" stroke="{scheme_style["color"]}" '
            f'stroke-width="2.5"{dash_attr} stroke-linecap="round" stroke-linejoin="round"/>'
        )

    legend_x = left + plot_w + 38
    legend_y = top + 34

    legend_rows = [
        "SCAPE-ZK",
        IIOT_SSI_NAME,
        "XAuth [6]",
        "SSL-XIoMT [8]",
    ]
    for idx, scheme in enumerate(legend_rows):
        lx = legend_x
        ly = legend_y + idx * 28
        scheme_style = style[scheme]
        dash_attr = f' stroke-dasharray="{scheme_style["dash"]}"' if scheme_style["dash"] else ""
        parts.append(
            f'  <line x1="{lx}" y1="{ly}" x2="{lx + 34}" y2="{ly}" stroke="{scheme_style["color"]}" '
            f'stroke-width="2.5"{dash_attr} stroke-linecap="round"/>'
        )
        parts.append(
            f'  <text x="{lx + 44}" y="{ly + 4}" class="legend">{escape(str(scheme_style["label"]))}</text>'
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
