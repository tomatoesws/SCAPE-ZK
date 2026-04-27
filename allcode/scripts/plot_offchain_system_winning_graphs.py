#!/usr/bin/env python3
"""
Generate five off-chain/system-level SCAPE-ZK comparison graphs.

No on-chain metrics are plotted. SCAPE-ZK curves are loaded from local
benchmark CSVs. Baseline curves are reconstructed from primitive equations in
baselines/offchain_system_primitive_equations.csv and calibrated with local
primitive timings from results/primitive_microbench.csv.
"""

from __future__ import annotations

import ast
import csv
import math
import operator
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatter


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures" / "offchain_system"
FIGS.mkdir(parents=True, exist_ok=True)

PRIMITIVES_CSV = RESULTS / "primitive_microbench.csv"
EQUATIONS_CSV = ROOT / "baselines" / "offchain_system_primitive_equations.csv"
CPABE_CSV = RESULTS / "cpabe_bench.csv"
GROTH16_CSV = RESULTS / "groth16_bench.csv"
PRE_CSV = RESULTS / "pre_bench.csv"
MERKLE_CSV = RESULTS / "merkle_bench.csv"
INTEGRITY_CSV = RESULTS / "integrity_filesize_bench.csv"

COLORS = {
    "SCAPE-ZK (Ours)": "#ff7f0e",
    "XAuth [6]": "#d62728",
    "SSL-XIoMT [8]": "#1f77b4",
    "Scheme [26]": "#2ca02c",
    "Traditional Re-encryption": "#7b3fb3",
}


class FormulaEvaluator(ast.NodeVisitor):
    OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    FUNCS = {
        "ceil": math.ceil,
        "ceil_log2": lambda x: math.ceil(math.log2(x)),
    }

    def __init__(self, variables: dict[str, float]) -> None:
        self.variables = variables

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant in formula: {node.value!r}")

    def visit_Name(self, node: ast.Name) -> float:
        if node.id not in self.variables:
            raise ValueError(f"Unknown formula variable: {node.id}")
        return float(self.variables[node.id])

    def visit_BinOp(self, node: ast.BinOp) -> float:
        op_type = type(node.op)
        if op_type not in self.OPS:
            raise ValueError(f"Unsupported formula operator: {op_type.__name__}")
        return self.OPS[op_type](self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        op_type = type(node.op)
        if op_type not in self.OPS:
            raise ValueError(f"Unsupported formula operator: {op_type.__name__}")
        return self.OPS[op_type](self.visit(node.operand))

    def visit_Call(self, node: ast.Call) -> float:
        if not isinstance(node.func, ast.Name) or node.func.id not in self.FUNCS:
            raise ValueError("Only ceil(...) and ceil_log2(...) are allowed in formulas")
        args = [self.visit(arg) for arg in node.args]
        return float(self.FUNCS[node.func.id](*args))

    def generic_visit(self, node: ast.AST) -> float:
        raise ValueError(f"Unsupported formula syntax: {type(node).__name__}")


def eval_formula(formula: str, variables: dict[str, float]) -> float:
    tree = ast.parse(formula, mode="eval")
    return FormulaEvaluator(variables).visit(tree)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def latest_rows(rows: list[dict[str, str]], *keys: str) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key not in grouped or row["timestamp"] > grouped[key]["timestamp"]:
            grouped[key] = row
    return list(grouped.values())


def primitive_values() -> dict[str, float]:
    prim: dict[str, float] = {}
    for row in read_rows(PRIMITIVES_CSV):
        name = row["primitive"]
        value = float(row["mean_ms"])
        if name.startswith("Thash "):
            prim["Thash32"] = value
        elif name.startswith("Tgrp "):
            prim["Tgrp"] = value
        elif name.startswith("Tpair "):
            prim["Tpair"] = value
        elif name.startswith("Tsym "):
            prim["Tsym_enc_1KB"] = value
        elif name == "Thash_1KB_sha256":
            prim["Thash_1KB"] = value
        elif name == "Tsym_dec_AES_256_GCM_1KB":
            prim["Tsym_dec_1KB"] = value
        elif name == "Tecc_verify_ECDSA_P256_SHA256":
            prim["Tecc_verify"] = value
        elif name == "Texp_G1_charm_SS512":
            prim["Texp_G1"] = value
        elif name == "Texp_GT_charm_SS512":
            prim["Texp_GT"] = value

    required = {
        "Thash32",
        "Tgrp",
        "Tpair",
        "Tsym_enc_1KB",
        "Thash_1KB",
        "Tsym_dec_1KB",
        "Tecc_verify",
        "Texp_G1",
        "Texp_GT",
    }
    missing = sorted(required - prim.keys())
    if missing:
        raise ValueError(f"Missing primitive measurements: {', '.join(missing)}")
    return prim


def equations_for(graph: str) -> list[dict[str, str]]:
    return [row for row in read_rows(EQUATIONS_CSV) if row["graph"] == graph]


def latest_metric(path: Path, filters: dict[str, str], value_col: str = "mean_ms") -> float:
    rows = read_rows(path)
    matches = [
        row for row in rows
        if all(row.get(key) == value for key, value in filters.items())
    ]
    if not matches:
        raise ValueError(f"Missing rows in {path} for {filters}")
    return float(max(matches, key=lambda row: row["timestamp"])[value_col])


def latest_cpabe_by_attr(operation: str, attrs: list[int]) -> dict[int, float]:
    rows = [
        row for row in read_rows(CPABE_CSV)
        if row["operation"] == operation and int(row["n_attrs"]) in attrs
    ]
    out: dict[int, float] = {}
    for attr in attrs:
        matches = [row for row in rows if int(row["n_attrs"]) == attr]
        if not matches:
            raise ValueError(f"Missing CP-ABE {operation} row for {attr} attrs")
        out[attr] = float(max(matches, key=lambda row: row["timestamp"])["mean_ms"])
    return out


def style_axes(ax: plt.Axes, xlabel: str, ylabel: str, title: str, logy: bool = False) -> None:
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(LogFormatter(labelOnlyBase=False))
    ax.grid(True, which="both", alpha=0.28)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)


def plot_series(
    ax: plt.Axes,
    x_values: list[int],
    y_values: list[float],
    label: str,
    linewidth: float = 2.2,
) -> None:
    ax.plot(
        x_values,
        y_values,
        color=COLORS[label],
        linewidth=linewidth,
        label=label,
    )


def use_categorical_x(ax: plt.Axes, labels: list[int]) -> list[int]:
    positions = list(range(len(labels)))
    ax.set_xticks(positions)
    ax.set_xticklabels([str(label) for label in labels])
    ax.set_xlim(-0.25, len(labels) - 0.75)
    return positions


def place_legend(ax: plt.Axes) -> None:
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


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGS / f"{stem}.png", dpi=300)
    fig.savefig(FIGS / f"{stem}.pdf")
    plt.close(fig)


def graph_authorization_preparation(prim: dict[str, float]) -> None:
    workloads = [1, 10, 50, 100, 200, 500]
    x = list(range(len(workloads)))
    t_session = latest_metric(GROTH16_CSV, {"circuit": "session", "metric": "prove_fullprove"})
    t_request = latest_metric(GROTH16_CSV, {"circuit": "request", "metric": "prove_fullprove"})
    scape_constant = t_session + t_request
    rows: list[dict[str, Any]] = []
    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    for eq in equations_for("authorization_preparation"):
        y = [eval_formula(eq["formula_ms"], prim | {"r": r}) for r in workloads]
        plot_series(ax, x, y, eq["scheme"])
        for r, value in zip(workloads, y):
            rows.append({"graph": "authorization_preparation", "scheme": eq["scheme"], "requests": r, "latency_ms": value, "basis": eq["formula_ms"]})
    scape_y = [scape_constant for _ in workloads]
    plot_series(ax, x, scape_y, "SCAPE-ZK (Ours)", linewidth=2.6)
    for r, value in zip(workloads, scape_y):
        rows.append({"graph": "authorization_preparation", "scheme": "SCAPE-ZK (Ours)", "requests": r, "latency_ms": value, "basis": "latest session prove_fullprove + latest request prove_fullprove; fixed-size batch circuit model"})
    style_axes(ax, "Workload (Number of Requests)", "Authorization Preparation Cost (ms)", "Off-chain Authorization Preparation Cost", logy=True)
    use_categorical_x(ax, workloads)
    place_legend(ax)
    save_figure(fig, "02_authorization_preparation_cost")
    write_rows(RESULTS / "offchain_system_graph_02_authorization_preparation.csv", rows)


def graph_cross_domain_delegation(prim: dict[str, float]) -> None:
    sizes = [1, 10, 20, 50, 100, 150, 200]
    x = list(range(len(sizes)))
    pre_const = latest_metric(PRE_CSV, {"operation": "re_encrypt"})
    rows: list[dict[str, Any]] = []
    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    eq = equations_for("cross_domain_delegation")[0]
    baseline_y = [eval_formula(eq["formula_ms"], prim | {"mb": mb}) for mb in sizes]
    plot_series(ax, x, baseline_y, eq["scheme"])
    for mb, value in zip(sizes, baseline_y):
        rows.append({"graph": "cross_domain_delegation", "scheme": eq["scheme"], "file_size_mb": mb, "latency_ms": value, "basis": eq["formula_ms"]})
    scape_y = [pre_const for _ in sizes]
    plot_series(ax, x, scape_y, "SCAPE-ZK (Ours)", linewidth=2.6)
    for mb, value in zip(sizes, scape_y):
        rows.append({"graph": "cross_domain_delegation", "scheme": "SCAPE-ZK (Ours)", "file_size_mb": mb, "latency_ms": value, "basis": "latest measured PRE re_encrypt mean from results/pre_bench.csv"})
    style_axes(ax, "File Size (MB)", "Delegation Latency (ms)", "Cross-Domain Delegation Latency", logy=True)
    use_categorical_x(ax, sizes)
    place_legend(ax)
    save_figure(fig, "03_cross_domain_delegation_latency")
    write_rows(RESULTS / "offchain_system_graph_03_cross_domain_delegation.csv", rows)


def write_equation_summary(prim: dict[str, float]) -> None:
    lines = [
        "# Off-chain/System Primitive Equations",
        "",
        "All baseline curves are reconstructed from `baselines/offchain_system_primitive_equations.csv`.",
        "All primitive timings are loaded from local benchmark CSVs.",
        "",
        "## Primitive Values",
        "",
    ]
    for name in sorted(prim):
        lines.append(f"- `{name}` = `{prim[name]:.9f}` ms")
    lines += ["", "## Baseline Equations", ""]
    for row in read_rows(EQUATIONS_CSV):
        lines.append(f"- Graph `{row['graph']}`, `{row['scheme']}`: `{row['formula_ms']}`")
    (RESULTS / "offchain_system_primitive_equations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 13,
        "legend.fontsize": 8.5,
        "figure.dpi": 180,
        "savefig.bbox": "tight",
    })
    prim = primitive_values()
    write_equation_summary(prim)
    graph_authorization_preparation(prim)
    graph_cross_domain_delegation(prim)
    print(f"Saved 2 off-chain/system graph PNG+PDF pairs under {FIGS}")
    print(f"Wrote equation summary to {RESULTS / 'offchain_system_primitive_equations.md'}")


if __name__ == "__main__":
    main()
