#!/usr/bin/env python3
"""Generate formula-derived computation-cost graphs for SCAPE_ZK_updated.pdf Table V.

The script uses verifier-side formulas extracted from the source papers and
calibrates their primitive terms with local benchmarks rather than reusing the
timings claimed in those papers.

    XAuth [6]      off-chain: n*(T_zk^v + T_merk(n))        on-chain: n * T_hash
    SSL-XIoMT [8]  off-chain: n*(T_zk^v + T_merk(n))        on-chain: n * T_hash
    IIoT SSI [30]  off-chain: n*T_zk^v + T_pair + n*T_grp   on-chain: n * T_hash
    SCAPE-ZK       off-chain: n * T_zk^v                    on-chain: T_pair

Primitive sources:
    T_zk^v   = mean Groth16 request verification time from paper/results/groth16_bench.csv
    T_pair   = mean BLS pairing_only time from paper/results/bls_bench.csv
    T_grp    = residual per-request group-operation cost derived from BLS verify_agg rows
    T_hash   = local SHA-256 timing calibration over a compact metadata-sized payload
    T_merk(n)= ceil(log2(max(n, 2))) * T_hash

Outputs:
    table_v_cost_components.csv
    table_v_total_cost_vs_requests.svg
    table_v_cost_breakdown_100req.svg
    table_v_onchain_offchain_100req.svg

This is a formula-derived estimator for the authorization-verification slice,
not a full integrated end-to-end benchmark.
"""

from __future__ import annotations

import csv
import hashlib
import math
import statistics
import time
from pathlib import Path
from xml.sax.saxutils import escape


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
RESULTS = PROJECT / "results"
OUT_CSV = HERE / "table_v_cost_components.csv"
OUT_TOTAL_SVG = HERE / "table_v_total_cost_vs_requests.svg"
OUT_BREAKDOWN_SVG = HERE / "table_v_cost_breakdown_100req.svg"
OUT_COMPONENT_SVG = HERE / "table_v_onchain_offchain_100req.svg"

LOADS = [1, 10, 50, 100, 200]
IIOT_SSI_NAME = (
    "Cross-Domain Identity Authentication Scheme for the IIoT Identification "
    "Resolution System Based on Self-Sovereign Identity [30]"
)
IIOT_SSI_LABEL = "IIoT SSI [30]"
SCHEMES = ["XAuth [6]", "SSL-XIoMT [8]", IIOT_SSI_NAME, "SCAPE-ZK"]

COLORS = {
    "XAuth [6]": "#455A64",
    "SSL-XIoMT [8]": "#007C89",
    IIOT_SSI_NAME: "#C4932F",
    "SCAPE-ZK": "#C2185B",
    "offchain": "#007C89",
    "onchain": "#D95F43",
    "grid": "#D8DDE3",
    "text": "#222831",
    "muted": "#66707A",
    "bg": "#FFFFFF",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean_request_verify_ms() -> float:
    rows = [
        row
        for row in read_csv(RESULTS / "groth16_bench.csv")
        if row["circuit"] == "request" and row["metric"] == "verify"
    ]
    if not rows:
        raise RuntimeError("No request verify rows found in groth16_bench.csv")
    return statistics.mean(float(row["mean_ms"]) for row in rows)


def bls_rows() -> list[dict[str, str]]:
    return read_csv(RESULTS / "bls_bench.csv")


def mean_pairing_ms() -> float:
    rows = [row for row in bls_rows() if row["operation"] == "pairing_only"]
    if not rows:
        raise RuntimeError("No pairing_only rows found in bls_bench.csv")
    return statistics.mean(float(row["mean_ms"]) for row in rows)


def residual_group_ms(pair_ms: float) -> float:
    residuals: list[float] = []
    for row in bls_rows():
        if row["operation"] != "verify_agg":
            continue
        n = int(row["batch_size"])
        if n <= 1:
            continue
        residual = max(float(row["mean_ms"]) - pair_ms, 0.0) / n
        residuals.append(residual)
    if not residuals:
        raise RuntimeError("No verify_agg rows found for deriving T_grp")
    return statistics.mean(residuals)


def hash_ms(rounds: int = 200_000) -> float:
    """Measure SHA-256 over a compact metadata leaf payload."""
    payload = b"CID:QmExample|tag:deadbeef|psi:policy|did:owner|time:1700000000"
    start = time.perf_counter()
    digest = b""
    for i in range(rounds):
        digest = hashlib.sha256(payload + i.to_bytes(4, "little", signed=False)).digest()
    elapsed = time.perf_counter() - start
    if digest == b"":
        raise RuntimeError("unreachable hash calibration guard")
    return (elapsed / rounds) * 1000.0


def merkle_verify_ms(n: int, hash_cost_ms: float) -> float:
    """Approximate one Merkle-path verification as one hash per tree level."""
    depth = max(1, math.ceil(math.log2(max(n, 2))))
    return depth * hash_cost_ms


def cost_rows() -> tuple[list[dict[str, float | int | str]], dict[str, float]]:
    t_zk_v = mean_request_verify_ms()
    t_pair = mean_pairing_ms()
    t_grp = residual_group_ms(t_pair)
    t_hash = hash_ms()
    primitives = {
        "T_zk_v_ms": t_zk_v,
        "T_pair_ms": t_pair,
        "T_grp_ms": t_grp,
        "T_hash_ms": t_hash,
    }

    rows: list[dict[str, float | int | str]] = []
    for n in LOADS:
        for scheme in SCHEMES:
            merk = merkle_verify_ms(n, t_hash)
            if scheme in {"XAuth [6]", "SSL-XIoMT [8]"}:
                offchain = n * (t_zk_v + merk)
                offchain_formula = "n*(T_zk^v + ceil(log2 n)*T_hash)"
            elif scheme == IIOT_SSI_NAME:
                offchain = (n * t_zk_v) + t_pair + (n * t_grp)
                offchain_formula = "n*T_zk^v + T_pair + n*T_grp"
            else:
                offchain = n * t_zk_v
                offchain_formula = "n*T_zk^v"

            if scheme == "SCAPE-ZK":
                onchain = t_pair
                onchain_formula = "T_pair"
            else:
                onchain = n * t_hash
                onchain_formula = "n*T_hash"

            rows.append(
                {
                    "n_requests": n,
                    "scheme": scheme,
                    "basis": "formula_derived",
                    "offchain_formula": offchain_formula,
                    "onchain_formula": onchain_formula,
                    "offchain_ms": offchain,
                    "onchain_ms": onchain,
                    "total_ms": offchain + onchain,
                    "T_merk_ms": merk,
                    **primitives,
                    "source_file": "results/groth16_bench.csv; results/bls_bench.csv; local SHA-256 calibration",
                    "source_filter_or_formula": f"offchain={offchain_formula}; onchain={onchain_formula}; T_merk(n)=ceil(log2(max(n,2)))*T_hash",
                    "notes": "Formula-derived authorization-verification slice estimator; not a full integrated baseline benchmark.",
                }
            )
    return rows, primitives


def write_cost_csv(rows: list[dict[str, float | int | str]]) -> None:
    fieldnames = [
        "n_requests",
        "scheme",
        "basis",
        "offchain_formula",
        "onchain_formula",
        "offchain_ms",
        "onchain_ms",
        "total_ms",
        "T_zk_v_ms",
        "T_pair_ms",
        "T_grp_ms",
        "T_hash_ms",
        "T_merk_ms",
        "source_file",
        "source_filter_or_formula",
        "notes",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: float) -> str:
    if value >= 1000:
        return f"{value / 1000:.2f}s"
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2f}"
    return f"{value:.4f}"


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'  <rect width="100%" height="100%" fill="{COLORS["bg"]}"/>',
        "  <style>",
        f'    text {{ font-family: Arial, Helvetica, sans-serif; fill: {COLORS["text"]}; }}',
        "    .title { font-size: 21px; font-weight: 700; }",
        f'    .subtitle {{ font-size: 12px; fill: {COLORS["muted"]}; }}',
        f'    .axis {{ font-size: 11px; fill: {COLORS["muted"]}; }}',
        "    .label { font-size: 12px; }",
        "    .value { font-size: 11px; font-weight: 700; }",
        "    .legend { font-size: 12px; }",
        f'    .grid {{ stroke: {COLORS["grid"]}; stroke-width: 1; }}',
        "    .axis-line { stroke: #9AA3AD; stroke-width: 1; }",
        "  </style>",
    ]


def write_svg(path: Path, parts: list[str]) -> None:
    path.write_text("\n".join(parts + ["</svg>"]) + "\n", encoding="utf-8")


def x_pos(n: int, x0: int, plot_w: int) -> float:
    return x0 + ((n - min(LOADS)) / (max(LOADS) - min(LOADS))) * plot_w


def y_pos_log(value: float, y0: int, plot_h: int, y_min: float, y_max: float) -> float:
    import math

    lv = math.log10(max(value, y_min))
    lmin = math.log10(y_min)
    lmax = math.log10(y_max)
    return y0 + plot_h - ((lv - lmin) / (lmax - lmin)) * plot_h


def draw_total_cost(rows: list[dict[str, float | int | str]], primitives: dict[str, float]) -> None:
    width = 980
    height = 620
    margin_left = 88
    margin_right = 48
    margin_top = 96
    margin_bottom = 112
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    y_min = 0.01
    y_max = max(float(row["total_ms"]) for row in rows) * 1.6

    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table V Computation-Cost Comparison</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">SCAPE_ZK_updated.pdf Table V terms only; primitive timings calibrated from local benchmark data</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Total estimated cost (ms, log scale)</text>',
        ]
    )

    ticks = [0.01, 0.1, 1, 10, 100, 1000, 5000]
    for tick in ticks:
        if tick > y_max:
            continue
        y = y_pos_log(tick, margin_top, plot_h, y_min, y_max)
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(tick)}</text>')

    for n in LOADS:
        x = x_pos(n, margin_left, plot_w)
        parts.append(f'  <line x1="{x:.1f}" y1="{margin_top + plot_h}" x2="{x:.1f}" y2="{margin_top + plot_h + 5}" class="axis-line"/>')
        parts.append(f'  <text x="{x:.1f}" y="{margin_top + plot_h + 23}" text-anchor="middle" class="axis">{n}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <text x="{margin_left + plot_w / 2}" y="{height - 56}" text-anchor="middle" class="axis">Number of authorization requests, n</text>')

    by_scheme: dict[str, list[dict[str, float | int | str]]] = {scheme: [] for scheme in SCHEMES}
    for row in rows:
        by_scheme[str(row["scheme"])].append(row)
    dash = {"XAuth [6]": "6 4", "SSL-XIoMT [8]": "", IIOT_SSI_NAME: "3 3", "SCAPE-ZK": ""}
    for scheme, scheme_rows in by_scheme.items():
        points = " ".join(
            f'{x_pos(int(row["n_requests"]), margin_left, plot_w):.1f},{y_pos_log(float(row["total_ms"]), margin_top, plot_h, y_min, y_max):.1f}'
            for row in scheme_rows
        )
        dash_attr = f' stroke-dasharray="{dash[scheme]}"' if dash[scheme] else ""
        parts.append(f'  <polyline points="{points}" fill="none" stroke="{COLORS[scheme]}" stroke-width="3"{dash_attr}/>')
        for row in scheme_rows:
            parts.append(
                f'  <circle cx="{x_pos(int(row["n_requests"]), margin_left, plot_w):.1f}" cy="{y_pos_log(float(row["total_ms"]), margin_top, plot_h, y_min, y_max):.1f}" r="4" fill="{COLORS[scheme]}"/>'
            )

    legend_y = height - 26
    for idx, scheme in enumerate(SCHEMES):
        x = margin_left + idx * 215
        dash_attr = f' stroke-dasharray="{dash[scheme]}"' if dash[scheme] else ""
        parts.append(f'  <line x1="{x}" y1="{legend_y}" x2="{x + 28}" y2="{legend_y}" stroke="{COLORS[scheme]}" stroke-width="3"{dash_attr}/>')
        parts.append(f'  <circle cx="{x + 14}" cy="{legend_y}" r="4" fill="{COLORS[scheme]}"/>')
        label = IIOT_SSI_LABEL if scheme == IIOT_SSI_NAME else scheme
        parts.append(f'  <text x="{x + 38}" y="{legend_y + 4}" class="legend">{escape(label)}</text>')

    primitive_note = (
        f'T_zk^v={primitives["T_zk_v_ms"]:.2f} ms, '
        f'T_pair={primitives["T_pair_ms"]:.2f} ms, '
        f'T_grp={primitives["T_grp_ms"]:.3f} ms, '
        f'T_hash={primitives["T_hash_ms"]:.6f} ms'
    )
    parts.append(f'  <text x="{margin_left}" y="{height - 78}" class="subtitle">{escape(primitive_note)}</text>')
    write_svg(OUT_TOTAL_SVG, parts)


def draw_breakdown(rows: list[dict[str, float | int | str]]) -> None:
    n_target = 100
    selected = [row for row in rows if int(row["n_requests"]) == n_target]
    width = 940
    height = 590
    margin_left = 92
    margin_right = 45
    margin_top = 92
    margin_bottom = 112
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    y_max = max(float(row["total_ms"]) for row in selected) * 1.2
    bar_gap = 40
    bar_w = (plot_w - bar_gap * (len(selected) + 1)) / len(selected)

    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table V Cost Breakdown at n={n_target}</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">Stacked off-chain and on-chain cost components; schemes limited to Table V</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Estimated cost (ms)</text>',
        ]
    )

    for i in range(6):
        value = y_max * i / 5
        y = margin_top + plot_h - (value / y_max) * plot_h
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(value)}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')

    for idx, row in enumerate(selected):
        x = margin_left + bar_gap + idx * (bar_w + bar_gap)
        off_h = (float(row["offchain_ms"]) / y_max) * plot_h
        on_h = (float(row["onchain_ms"]) / y_max) * plot_h
        y_off = margin_top + plot_h - off_h
        y_on = y_off - on_h
        cx = x + bar_w / 2
        parts.append(f'  <rect x="{x:.1f}" y="{y_off:.1f}" width="{bar_w:.1f}" height="{off_h:.1f}" rx="3" fill="{COLORS["offchain"]}"/>')
        if on_h >= 1.0:
            parts.append(f'  <rect x="{x:.1f}" y="{y_on:.1f}" width="{bar_w:.1f}" height="{on_h:.1f}" rx="3" fill="{COLORS["onchain"]}"/>')
        else:
            parts.append(f'  <line x1="{x:.1f}" y1="{y_off:.1f}" x2="{x + bar_w:.1f}" y2="{y_off:.1f}" stroke="{COLORS["onchain"]}" stroke-width="2"/>')
        parts.append(f'  <text x="{cx:.1f}" y="{y_on - 8:.1f}" text-anchor="middle" class="value">{fmt(float(row["total_ms"]))}</text>')
        label = IIOT_SSI_LABEL if row["scheme"] == IIOT_SSI_NAME else str(row["scheme"])
        parts.append(f'  <text x="{cx:.1f}" y="{margin_top + plot_h + 25}" text-anchor="middle" class="label">{escape(label)}</text>')

    legend_y = height - 34
    parts.append(f'  <rect x="{margin_left}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{COLORS["offchain"]}"/>')
    parts.append(f'  <text x="{margin_left + 20}" y="{legend_y}" class="legend">Off-chain Table V cost</text>')
    parts.append(f'  <rect x="{margin_left + 210}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{COLORS["onchain"]}"/>')
    parts.append(f'  <text x="{margin_left + 230}" y="{legend_y}" class="legend">On-chain Table V cost</text>')
    write_svg(OUT_BREAKDOWN_SVG, parts)


def draw_component_comparison(rows: list[dict[str, float | int | str]]) -> None:
    n_target = 100
    selected = [row for row in rows if int(row["n_requests"]) == n_target]
    width = 1080
    height = 620
    margin_left = 92
    margin_right = 45
    margin_top = 92
    margin_bottom = 120
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    y_min = 0.01
    y_max = max(float(row["offchain_ms"]) for row in selected) * 1.25
    scheme_gap = 42
    pair_gap = 10
    group_w = (plot_w - scheme_gap * (len(selected) + 1)) / len(selected)
    bar_w = (group_w - pair_gap) / 2

    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table V Off-Chain vs On-Chain Cost at n={n_target}</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">Formula-derived comparison from source-paper verifier equations with shared local primitive calibration</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Estimated cost (ms, log scale)</text>',
        ]
    )

    ticks = [0.01, 0.1, 1, 10, 100, 1000, 5000]
    for tick in ticks:
        if tick > y_max:
            continue
        y = y_pos_log(tick, margin_top, plot_h, y_min, y_max)
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(tick)}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')

    for idx, row in enumerate(selected):
        group_x = margin_left + scheme_gap + idx * (group_w + scheme_gap)
        offchain = float(row["offchain_ms"])
        onchain = float(row["onchain_ms"])
        bars = [
            ("Off-chain", offchain, COLORS["offchain"]),
            ("On-chain", onchain, COLORS["onchain"]),
        ]

        for bar_idx, (label, value, color) in enumerate(bars):
            x = group_x + bar_idx * (bar_w + pair_gap)
            y = y_pos_log(value, margin_top, plot_h, y_min, y_max)
            height_px = (margin_top + plot_h) - y
            parts.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height_px:.1f}" rx="3" fill="{color}"/>')
            parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="value">{fmt(value)}</text>')
            parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{margin_top + plot_h + 22}" text-anchor="middle" class="axis">{label}</text>')

        parts.append(
            f'  <text x="{group_x + group_w / 2:.1f}" y="{margin_top + plot_h + 48}" text-anchor="middle" class="label">{escape(IIOT_SSI_LABEL if row["scheme"] == IIOT_SSI_NAME else str(row["scheme"]))}</text>'
        )

    legend_y = height - 34
    parts.append(f'  <rect x="{margin_left}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{COLORS["offchain"]}"/>')
    parts.append(f'  <text x="{margin_left + 20}" y="{legend_y}" class="legend">Off-chain Table V cost</text>')
    parts.append(f'  <rect x="{margin_left + 220}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{COLORS["onchain"]}"/>')
    parts.append(f'  <text x="{margin_left + 240}" y="{legend_y}" class="legend">On-chain Table V cost</text>')
    write_svg(OUT_COMPONENT_SVG, parts)


def write_readme(primitives: dict[str, float]) -> None:
    readme = f"""# Table V Computation-Cost Benchmark

Source: `SCAPE_ZK_updated.pdf`, Table V, "Authorization Verification Scalability".

This folder contains code and generated artifacts for a formula-derived computation-cost comparison aligned with the Table V scope.

Generated files:

- `table_v_cost_components.csv`
- `table_v_total_cost_vs_requests.svg`
- `table_v_cost_breakdown_100req.svg`
- `table_v_onchain_offchain_100req.svg`
- `generate_table_v_cost_graphs.py`

Primitive calibration:

- `T_zk^v`: {primitives["T_zk_v_ms"]:.4f} ms, from `paper/results/groth16_bench.csv` request verification rows.
- `T_pair`: {primitives["T_pair_ms"]:.4f} ms, from `paper/results/bls_bench.csv` `pairing_only` rows.
- `T_grp`: {primitives["T_grp_ms"]:.4f} ms, derived from BLS aggregate verification residual `(verify_agg - T_pair) / n`.
- `T_hash`: {primitives["T_hash_ms"]:.8f} ms, local SHA-256 metadata-leaf calibration.

Formula mapping used:

- XAuth [6]: off-chain `n*(T_zk^v + ceil(log2 n)*T_hash)` from anonymous-proof verification plus MMHT correctness validation; on-chain `n*T_hash` from control-layer hash anchoring.
- SSL-XIoMT [8]: off-chain `n*(T_zk^v + ceil(log2 n)*T_hash)` from `ver_merkle_proof(...)` and `_ZKP_valid(...)` / `check_ZKP_validity(...)`; on-chain `n*T_hash` from Hyperledger Merkle-root anchoring.
- Cross-Domain Identity Authentication Scheme for the IIoT Identification Resolution System Based on Self-Sovereign Identity [30]: off-chain `n*T_zk^v + T_pair + n*T_grp` from verifier-side proof checks plus batch pairing equation (5)/(6); on-chain `n*T_hash` from blockchain authentication-record anchoring.
- SCAPE-ZK: off-chain `n*T_zk^v`; on-chain `T_pair`.

Scope note:

This estimator does not reuse the timing numbers claimed in the comparator papers. It applies the extracted formulas to a shared local primitive calibration so the graph reflects structural cost differences under one measurement basis.
"""
    (HERE / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    rows, primitives = cost_rows()
    write_cost_csv(rows)
    draw_total_cost(rows, primitives)
    draw_breakdown(rows)
    draw_component_comparison(rows)
    write_readme(primitives)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_TOTAL_SVG}")
    print(f"Wrote {OUT_BREAKDOWN_SVG}")
    print(f"Wrote {OUT_COMPONENT_SVG}")


if __name__ == "__main__":
    main()
