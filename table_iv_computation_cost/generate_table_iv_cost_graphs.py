#!/usr/bin/env python3
"""Generate computation-cost comparison graphs for SCAPE_ZK_updated.pdf Table IV.

The script evaluates only the cost columns shown in Table IV:

    Proof Gen
    Amortized Proof
    Encrypt
    Proof Ver
    Integrity & Delegation Verification

It uses local SCAPE-ZK primitive measurements where available and small local
calibrations for hash/Merkle/ECC-like operations. The output is a reproducible
benchmark/estimator for Table-IV terms, not a reimplementation of every
baseline protocol.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import statistics
import time
from pathlib import Path
from xml.sax.saxutils import escape


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
RESULTS = PROJECT / "paper" / "results"

OUT_COMPONENTS = HERE / "table_iv_cost_components.csv"
OUT_PRIMITIVES = HERE / "table_iv_primitive_benchmarks.csv"
OUT_TOTAL_SVG = HERE / "table_iv_total_cost_vs_requests.svg"
OUT_BREAKDOWN_SVG = HERE / "table_iv_component_breakdown.svg"
OUT_COLUMNS_SVG = HERE / "table_iv_columns_at_n.svg"

SCHEMES = ["XAuth [6]", "SSL-XIoMT [8]", "Scheme [30]", "SCAPE-ZK"]
LOADS = [1, 5, 10, 25, 50, 100, 200]

COLORS = {
    "XAuth [6]": "#455A64",
    "SSL-XIoMT [8]": "#007C89",
    "Scheme [30]": "#C4932F",
    "SCAPE-ZK": "#C2185B",
    "amortized_proof": "#007C89",
    "encrypt": "#4C8B56",
    "proof_verify": "#D95F43",
    "integrity_delegation": "#2F455C",
    "grid": "#D8DDE3",
    "text": "#222831",
    "muted": "#66707A",
    "bg": "#FFFFFF",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean_rows(path: Path, **filters: str) -> float:
    rows = read_csv(path)
    selected = [
        float(row["mean_ms"])
        for row in rows
        if all(row.get(key) == value for key, value in filters.items())
    ]
    if not selected:
        desc = ", ".join(f"{k}={v}" for k, v in filters.items())
        raise RuntimeError(f"No rows found in {path} for {desc}")
    return statistics.mean(selected)


def latest_attr_value(operation: str, n_attrs: int) -> float:
    rows = [
        row
        for row in read_csv(RESULTS / "cpabe_bench.csv")
        if row["operation"] == operation and int(row["n_attrs"]) == n_attrs
    ]
    if not rows:
        raise RuntimeError(f"No CP-ABE row for operation={operation}, n_attrs={n_attrs}")
    return float(rows[-1]["mean_ms"])


def bls_values() -> tuple[float, float]:
    rows = read_csv(RESULTS / "bls_bench.csv")
    pairing = statistics.mean(float(row["mean_ms"]) for row in rows if row["operation"] == "pairing_only")
    residuals: list[float] = []
    for row in rows:
        if row["operation"] != "verify_agg":
            continue
        batch_size = int(row["batch_size"])
        if batch_size <= 1:
            continue
        residuals.append(max(float(row["mean_ms"]) - pairing, 0.0) / batch_size)
    if not residuals:
        raise RuntimeError("Could not derive T_grp from bls_bench.csv")
    return pairing, statistics.mean(residuals)


def pre_verify_value() -> float:
    # The PRE benchmark exposes transform/decrypt phases, not a separately named
    # verifier. Use the lightest validation-like PRE phase as T_pre^v proxy.
    rows = read_csv(RESULTS / "pre_bench.csv")
    for op in ("decrypt_re", "re_encrypt"):
        selected = [float(row["mean_ms"]) for row in rows if row["operation"] == op]
        if selected:
            return statistics.mean(selected)
    raise RuntimeError("No PRE rows available for T_pre^v proxy")


def calibrate_hash_ms(payload_size: int, rounds: int) -> float:
    payload = bytes((i % 251 for i in range(payload_size)))
    digest = b""
    start = time.perf_counter()
    for i in range(rounds):
        digest = hashlib.sha256(payload + i.to_bytes(4, "little", signed=False)).digest()
    elapsed = time.perf_counter() - start
    if not digest:
        raise RuntimeError("unreachable hash calibration guard")
    return elapsed * 1000.0 / rounds


def calibrate_merkle_ms(leaf_size: int, depth: int, rounds: int) -> float:
    leaf = bytes((i % 199 for i in range(leaf_size)))
    siblings = [hashlib.sha256(f"sibling-{i}".encode("ascii")).digest() for i in range(depth)]
    digest = b""
    start = time.perf_counter()
    for i in range(rounds):
        digest = hashlib.sha256(leaf + i.to_bytes(4, "little", signed=False)).digest()
        for sibling in siblings:
            digest = hashlib.sha256(digest + sibling).digest()
    elapsed = time.perf_counter() - start
    if not digest:
        raise RuntimeError("unreachable Merkle calibration guard")
    return elapsed * 1000.0 / rounds


def calibrate_ecc_encrypt_proxy_ms(rounds: int) -> float:
    """Calibrate an ECC-encryption proxy without external dependencies.

    If the cryptography package is available, run real ECDH key exchange on
    SECP256R1. Otherwise use a fixed-size modular exponentiation proxy. The
    fallback is intentionally labeled as a proxy in the output CSV.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend

        peer_private = ec.generate_private_key(ec.SECP256R1(), default_backend())
        peer_public = peer_private.public_key()
        start = time.perf_counter()
        secret = b""
        for _ in range(rounds):
            private = ec.generate_private_key(ec.SECP256R1(), default_backend())
            secret = private.exchange(ec.ECDH(), peer_public)
        elapsed = time.perf_counter() - start
        if not secret:
            raise RuntimeError("unreachable ECDH calibration guard")
        return elapsed * 1000.0 / rounds
    except Exception:
        prime = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        generator = 5
        start = time.perf_counter()
        value = 0
        for i in range(rounds):
            value = pow(generator, 0xA5A5A5A5A5A5A5A5 + i, prime)
        elapsed = time.perf_counter() - start
        if value == 0:
            raise RuntimeError("unreachable scalar proxy calibration guard")
        return elapsed * 1000.0 / rounds


def primitive_values(n_attrs: int, rounds: int) -> dict[str, float]:
    request_prove = mean_rows(RESULTS / "groth16_bench.csv", circuit="request", metric="prove_fullprove")
    session_prove = mean_rows(RESULTS / "groth16_bench.csv", circuit="session", metric="prove_fullprove")
    request_verify = mean_rows(RESULTS / "groth16_bench.csv", circuit="request", metric="verify")
    attr_circuit = f"session_{n_attrs}"
    attr_rows = [
        float(row["mean_ms"])
        for row in read_csv(RESULTS / "groth16_bench.csv")
        if row["circuit"] == attr_circuit and row["metric"] == "prove_fullprove"
    ]
    attr_prove = statistics.mean(attr_rows) if attr_rows else session_prove
    pair, group = bls_values()
    return {
        "T_zk_g_Cid_ms": request_prove,
        "T_zk_g_Cattr_ms": attr_prove,
        "T_zk_g_generic_ms": request_prove,
        "T_zk_g_Creq_ms": request_prove,
        "T_zk_g_Csess_ms": session_prove,
        "T_zk_v_ms": request_verify,
        "T_sym_enc_ms": latest_attr_value("sym_encrypt_1KB", n_attrs),
        "T_abe_enc_ms": latest_attr_value("cpabe_encrypt", n_attrs),
        "T_ecc_enc_ms": calibrate_ecc_encrypt_proxy_ms(max(rounds // 80, 200)),
        "T_pair_ms": pair,
        "T_grp_ms": group,
        "T_hash_ms": calibrate_hash_ms(8192, rounds),
        "T_hash_l_ms": calibrate_hash_ms(128, rounds),
        "T_merk_ms": calibrate_merkle_ms(8192, 16, max(rounds // 5, 1000)),
        "T_merk_star_ms": calibrate_merkle_ms(128, 16, max(rounds // 5, 1000)),
        "T_pre_v_ms": pre_verify_value(),
    }


def component_rows(primitives: dict[str, float]) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for n in LOADS:
        scheme_values = {
            "XAuth [6]": {
                "proof_gen_formula": "T_zk^g(|C_id|)",
                "amortized_formula": "T_zk^g(|C_id|)",
                "encrypt_formula": "--",
                "proof_verify_formula": "T_zk^v",
                "integrity_formula": "T_merk + T_hash",
                "proof_gen_ms": primitives["T_zk_g_Cid_ms"],
                "amortized_proof_ms": primitives["T_zk_g_Cid_ms"],
                "encrypt_ms": 0.0,
                "proof_verify_ms": primitives["T_zk_v_ms"],
                "integrity_delegation_ms": primitives["T_merk_ms"] + primitives["T_hash_ms"],
            },
            "SSL-XIoMT [8]": {
                "proof_gen_formula": "T_zk^g(|C_attr|)",
                "amortized_formula": "T_zk^g(|C_attr|)",
                "encrypt_formula": "T_sym_enc + T_abe_enc + T_ecc_enc",
                "proof_verify_formula": "T_zk^v",
                "integrity_formula": "T_merk + T_hash",
                "proof_gen_ms": primitives["T_zk_g_Cattr_ms"],
                "amortized_proof_ms": primitives["T_zk_g_Cattr_ms"],
                "encrypt_ms": primitives["T_sym_enc_ms"] + primitives["T_abe_enc_ms"] + primitives["T_ecc_enc_ms"],
                "proof_verify_ms": primitives["T_zk_v_ms"],
                "integrity_delegation_ms": primitives["T_merk_ms"] + primitives["T_hash_ms"],
            },
            "Scheme [30]": {
                "proof_gen_formula": "T_zk^g",
                "amortized_formula": "O(T_pair + n*T_grp) / n",
                "encrypt_formula": "--",
                "proof_verify_formula": "T_zk^v + O(T_pair + n*T_grp) / n",
                "integrity_formula": "T_hash",
                "proof_gen_ms": primitives["T_zk_g_generic_ms"],
                "amortized_proof_ms": (primitives["T_pair_ms"] + n * primitives["T_grp_ms"]) / n,
                "encrypt_ms": 0.0,
                "proof_verify_ms": primitives["T_zk_v_ms"] + (primitives["T_pair_ms"] + n * primitives["T_grp_ms"]) / n,
                "integrity_delegation_ms": primitives["T_hash_ms"],
            },
            "SCAPE-ZK": {
                "proof_gen_formula": "T_zk^g(|C_req|)",
                "amortized_formula": "(T_zk^g(|C_sess|) + n*T_zk^g(|C_req|)) / n",
                "encrypt_formula": "T_sym_enc + T_abe_enc",
                "proof_verify_formula": "T_zk^v",
                "integrity_formula": "T_merk* + T_hash^ell + T_pre^v",
                "proof_gen_ms": primitives["T_zk_g_Creq_ms"],
                "amortized_proof_ms": (primitives["T_zk_g_Csess_ms"] + n * primitives["T_zk_g_Creq_ms"]) / n,
                "encrypt_ms": primitives["T_sym_enc_ms"] + primitives["T_abe_enc_ms"],
                "proof_verify_ms": primitives["T_zk_v_ms"],
                "integrity_delegation_ms": primitives["T_merk_star_ms"] + primitives["T_hash_l_ms"] + primitives["T_pre_v_ms"],
            },
        }
        for scheme in SCHEMES:
            values = scheme_values[scheme]
            per_request = (
                float(values["amortized_proof_ms"])
                + float(values["encrypt_ms"])
                + float(values["proof_verify_ms"])
                + float(values["integrity_delegation_ms"])
            )
            rows.append(
                {
                    "n_requests": n,
                    "scheme": scheme,
                    "basis": "primitive_calibrated_estimator",
                    **values,
                    "per_request_total_ms": per_request,
                    "batch_total_ms": per_request * n,
                    "source_file": "paper/results/groth16_bench.csv; paper/results/cpabe_bench.csv; paper/results/bls_bench.csv; paper/results/pre_bench.csv; local hash/Merkle/ECC calibrations",
                    "source_filter_or_formula": (
                        f"amortized={values['amortized_formula']}; "
                        f"encrypt={values['encrypt_formula']}; "
                        f"proof_verify={values['proof_verify_formula']}; "
                        f"integrity={values['integrity_formula']}"
                    ),
                    "notes": "Table IV analytical/proxy estimator calibrated with local primitives; not a full-system baseline reimplementation.",
                }
            )
    return rows


def write_csvs(rows: list[dict[str, float | int | str]], primitives: dict[str, float]) -> None:
    with OUT_PRIMITIVES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["primitive", "mean_ms", "source"])
        writer.writeheader()
        sources = {
            "T_zk_g_Cid_ms": "groth16_bench.csv request prove proxy",
            "T_zk_g_Cattr_ms": "groth16_bench.csv session_n_attrs prove proxy",
            "T_zk_g_generic_ms": "groth16_bench.csv request prove proxy",
            "T_zk_g_Creq_ms": "groth16_bench.csv request prove",
            "T_zk_g_Csess_ms": "groth16_bench.csv session prove",
            "T_zk_v_ms": "groth16_bench.csv request verify",
            "T_sym_enc_ms": "cpabe_bench.csv sym_encrypt_1KB",
            "T_abe_enc_ms": "cpabe_bench.csv cpabe_encrypt",
            "T_ecc_enc_ms": "local ECDH or scalar-multiplication proxy",
            "T_pair_ms": "bls_bench.csv pairing_only",
            "T_grp_ms": "derived residual from bls_bench.csv verify_agg",
            "T_hash_ms": "local SHA-256 over 8 KiB payload",
            "T_hash_l_ms": "local SHA-256 over 128 B metadata payload",
            "T_merk_ms": "local Merkle path over 8 KiB leaf",
            "T_merk_star_ms": "local Merkle path over 128 B compact leaf",
            "T_pre_v_ms": "pre_bench.csv decrypt_re proxy",
        }
        for primitive, value in primitives.items():
            writer.writerow({"primitive": primitive, "mean_ms": value, "source": sources.get(primitive, "")})

    fieldnames = [
        "n_requests",
        "scheme",
        "basis",
        "proof_gen_formula",
        "amortized_formula",
        "encrypt_formula",
        "proof_verify_formula",
        "integrity_formula",
        "proof_gen_ms",
        "amortized_proof_ms",
        "encrypt_ms",
        "proof_verify_ms",
        "integrity_delegation_ms",
        "per_request_total_ms",
        "batch_total_ms",
        "source_file",
        "source_filter_or_formula",
        "notes",
    ]
    with OUT_COMPONENTS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: float) -> str:
    if value >= 1000:
        return f"{value / 1000:.2f}s"
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2f}"
    return f"{value:.3f}"


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


def draw_total_vs_requests(rows: list[dict[str, float | int | str]]) -> None:
    import math

    width = 980
    height = 620
    margin_left = 88
    margin_right = 48
    margin_top = 96
    margin_bottom = 112
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    y_min = 1.0
    y_max = max(float(row["batch_total_ms"]) for row in rows) * 1.45

    def y_pos(value: float) -> float:
        lv = math.log10(max(value, y_min))
        lmin = math.log10(y_min)
        lmax = math.log10(y_max)
        return margin_top + plot_h - ((lv - lmin) / (lmax - lmin)) * plot_h

    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table IV Computation Cost vs Request Count</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">Batch total from Table IV columns only; y-axis uses log scale</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Batch total cost (ms)</text>',
        ]
    )
    for tick in [1, 10, 100, 1000, 10000, 100000]:
        if tick > y_max:
            continue
        y = y_pos(tick)
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(tick)}</text>')
    for n in LOADS:
        x = x_pos(n, margin_left, plot_w)
        parts.append(f'  <line x1="{x:.1f}" y1="{margin_top + plot_h}" x2="{x:.1f}" y2="{margin_top + plot_h + 5}" class="axis-line"/>')
        parts.append(f'  <text x="{x:.1f}" y="{margin_top + plot_h + 23}" text-anchor="middle" class="axis">{n}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <text x="{margin_left + plot_w / 2}" y="{height - 54}" text-anchor="middle" class="axis">Number of requests in the batch/session</text>')

    for scheme in SCHEMES:
        scheme_rows = [row for row in rows if row["scheme"] == scheme]
        points = " ".join(
            f'{x_pos(int(row["n_requests"]), margin_left, plot_w):.1f},{y_pos(float(row["batch_total_ms"])):.1f}'
            for row in scheme_rows
        )
        parts.append(f'  <polyline points="{points}" fill="none" stroke="{COLORS[scheme]}" stroke-width="3"/>')
        for row in scheme_rows:
            x = x_pos(int(row["n_requests"]), margin_left, plot_w)
            y = y_pos(float(row["batch_total_ms"]))
            parts.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{COLORS[scheme]}"/>')

    legend_y = height - 24
    for idx, scheme in enumerate(SCHEMES):
        x = margin_left + idx * 210
        parts.append(f'  <line x1="{x}" y1="{legend_y}" x2="{x + 28}" y2="{legend_y}" stroke="{COLORS[scheme]}" stroke-width="3"/>')
        parts.append(f'  <circle cx="{x + 14}" cy="{legend_y}" r="4" fill="{COLORS[scheme]}"/>')
        parts.append(f'  <text x="{x + 38}" y="{legend_y + 4}" class="legend">{escape(scheme)}</text>')
    write_svg(OUT_TOTAL_SVG, parts)


def draw_component_breakdown(rows: list[dict[str, float | int | str]], n_requests: int) -> None:
    selected = [row for row in rows if int(row["n_requests"]) == n_requests]
    width = 1000
    height = 620
    margin_left = 92
    margin_right = 48
    margin_top = 96
    margin_bottom = 124
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    components = [
        ("amortized_proof_ms", "Amortized proof", "amortized_proof"),
        ("encrypt_ms", "Encrypt", "encrypt"),
        ("proof_verify_ms", "Proof verify", "proof_verify"),
        ("integrity_delegation_ms", "Integrity/delegation", "integrity_delegation"),
    ]
    y_max = max(float(row["per_request_total_ms"]) for row in selected) * 1.2
    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table IV Per-Request Component Breakdown</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">n={n_requests}; stacked bars use only Table IV cost columns</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Per-request cost (ms)</text>',
        ]
    )
    for i in range(6):
        value = y_max * i / 5
        y = margin_top + plot_h - (value / y_max) * plot_h
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(value)}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')

    gap = 54
    bar_w = (plot_w - gap * (len(selected) + 1)) / len(selected)
    for idx, row in enumerate(selected):
        x = margin_left + gap + idx * (bar_w + gap)
        current_y = margin_top + plot_h
        for key, _, color_key in components:
            value = float(row[key])
            h = (value / y_max) * plot_h
            current_y -= h
            if h > 0:
                parts.append(f'  <rect x="{x:.1f}" y="{current_y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{COLORS[color_key]}"/>')
        parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{current_y - 8:.1f}" text-anchor="middle" class="value">{fmt(float(row["per_request_total_ms"]))}</text>')
        parts.append(f'  <text x="{x + bar_w / 2:.1f}" y="{margin_top + plot_h + 24}" text-anchor="middle" class="label">{escape(str(row["scheme"]))}</text>')

    legend_y = height - 42
    for idx, (_, label, color_key) in enumerate(components):
        x = margin_left + idx * 215
        parts.append(f'  <rect x="{x}" y="{legend_y - 11}" width="13" height="13" fill="{COLORS[color_key]}"/>')
        parts.append(f'  <text x="{x + 20}" y="{legend_y}" class="legend">{escape(label)}</text>')
    write_svg(OUT_BREAKDOWN_SVG, parts)


def draw_table_columns(rows: list[dict[str, float | int | str]], n_requests: int) -> None:
    selected = [row for row in rows if int(row["n_requests"]) == n_requests]
    width = 1120
    height = 640
    margin_left = 92
    margin_right = 44
    margin_top = 96
    margin_bottom = 132
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    columns = [
        ("proof_gen_ms", "Proof Gen", "#455A64"),
        ("amortized_proof_ms", "Amortized", "#007C89"),
        ("encrypt_ms", "Encrypt", "#4C8B56"),
        ("proof_verify_ms", "Proof Ver", "#D95F43"),
        ("integrity_delegation_ms", "Integrity/Deleg.", "#2F455C"),
    ]
    y_max = max(float(row[key]) for row in selected for key, _, _ in columns) * 1.18
    parts = svg_header(width, height)
    parts.extend(
        [
            f'  <text x="{margin_left}" y="38" class="title">Table IV Cost Columns</text>',
            f'  <text x="{margin_left}" y="60" class="subtitle">n={n_requests}; one bar per Table IV computation-cost column</text>',
            f'  <text x="24" y="{margin_top + plot_h / 2}" class="axis" transform="rotate(-90 24 {margin_top + plot_h / 2})">Cost (ms)</text>',
        ]
    )
    for i in range(6):
        value = y_max * i / 5
        y = margin_top + plot_h - (value / y_max) * plot_h
        parts.append(f'  <line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'  <text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt(value)}</text>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{width - margin_right}" y2="{margin_top + plot_h}" class="axis-line"/>')
    parts.append(f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" class="axis-line"/>')

    group_gap = 52
    group_w = (plot_w - group_gap * (len(selected) + 1)) / len(selected)
    inner_gap = 6
    bar_w = (group_w - inner_gap * (len(columns) - 1)) / len(columns)
    for row_idx, row in enumerate(selected):
        group_x = margin_left + group_gap + row_idx * (group_w + group_gap)
        for col_idx, (key, _, color) in enumerate(columns):
            value = float(row[key])
            x = group_x + col_idx * (bar_w + inner_gap)
            bar_h = (value / y_max) * plot_h
            y = margin_top + plot_h - bar_h
            if bar_h > 0:
                parts.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="2" fill="{color}"/>')
        parts.append(f'  <text x="{group_x + group_w / 2:.1f}" y="{margin_top + plot_h + 24}" text-anchor="middle" class="label">{escape(str(row["scheme"]))}</text>')

    legend_y = height - 48
    for idx, (_, label, color) in enumerate(columns):
        x = margin_left + idx * 178
        parts.append(f'  <rect x="{x}" y="{legend_y - 11}" width="13" height="13" rx="2" fill="{color}"/>')
        parts.append(f'  <text x="{x + 20}" y="{legend_y}" class="legend">{escape(label)}</text>')
    write_svg(OUT_COLUMNS_SVG, parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Table IV computation-cost comparison graphs.")
    parser.add_argument("--attrs", type=int, default=50, choices=[5, 10, 20, 50], help="Attribute count for CP-ABE/ZKP attribute proxy.")
    parser.add_argument("--breakdown-n", type=int, default=50, choices=LOADS, help="Request count for stacked component breakdown.")
    parser.add_argument("--rounds", type=int, default=120_000, help="Calibration rounds for hash-style primitives.")
    args = parser.parse_args()

    primitives = primitive_values(args.attrs, args.rounds)
    rows = component_rows(primitives)
    write_csvs(rows, primitives)
    draw_total_vs_requests(rows)
    draw_component_breakdown(rows, args.breakdown_n)
    draw_table_columns(rows, args.breakdown_n)
    print(f"Wrote {OUT_PRIMITIVES}")
    print(f"Wrote {OUT_COMPONENTS}")
    print(f"Wrote {OUT_TOTAL_SVG}")
    print(f"Wrote {OUT_BREAKDOWN_SVG}")
    print(f"Wrote {OUT_COLUMNS_SVG}")


if __name__ == "__main__":
    main()
