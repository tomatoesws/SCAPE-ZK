#!/usr/bin/env python3
"""Parse Caliper txInfo JSON logs and compute latency percentiles."""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path


ROUND_LABELS = [
    "register-100tx",
    "register-500tx",
    "register-1000tx",
    "verifyproof-100tx",
    "verifyproof-500tx",
    "verifyproof-1000tx",
    "revoke-100tx",
    "revoke-500tx",
    "revoke-1000tx",
    "updatecred-100tx",
    "updatecred-500tx",
    "updatecred-1000tx",
    "recordexists-100tx",
    "recordexists-500tx",
    "recordexists-1000tx",
]

JSON_RE = re.compile(r"(\{\"status\":.*\})")
START_RE = re.compile(r"Started round \d+ \(([^)]+)\)")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = math.ceil((pct / 100.0) * len(ordered))
    return ordered[max(0, min(rank - 1, len(ordered) - 1))]


def parse_trial(log_path: Path) -> dict[str, list[float]]:
    by_round: dict[str, list[float]] = defaultdict(list)
    current_label = None
    for line in log_path.read_text(errors="replace").splitlines():
        start_match = START_RE.search(line)
        if start_match:
            current_label = start_match.group(1)
            continue

        match = JSON_RE.search(line)
        if not match:
            continue
        row = json.loads(match.group(1))
        status = row["status"]
        if status["status"] != "success":
            continue
        if current_label is None:
            continue
        by_round[current_label].append(status["time_final"] - status["time_create"])
    return by_round


def parse_caliper_rows(log_path: Path) -> dict[str, dict[str, float | int]]:
    rows = {}
    for line in log_path.read_text(errors="replace").splitlines():
        if "tx" not in line or "|" not in line:
            continue
        line = line[line.find("|") :]
        parts = [part.strip() for part in line.split("|")]
        parts = [part for part in parts if part]
        if len(parts) != 8 or parts[0] == "Name" or set(parts[0]) == {"-"}:
            continue
        name = parts[0]
        if name not in ROUND_LABELS:
            continue
        rows[name] = {
            "succ": int(parts[1]),
            "fail": int(parts[2]),
            "send_rate_tps": float(parts[3]),
            "max_latency_s_report": float(parts[4]),
            "min_latency_s_report": float(parts[5]),
            "avg_latency_s_report": float(parts[6]),
            "throughput_tps": float(parts[7]),
        }
    return rows


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else math.nan


def sd(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: parse_txlog_percentiles.py OUTPUT.csv LOG...", file=sys.stderr)
        return 2

    output = Path(sys.argv[1])
    logs = [Path(arg) for arg in sys.argv[2:]]
    rows = []

    for trial_index, log_path in enumerate(logs, start=1):
        by_round = parse_trial(log_path)
        caliper_rows = parse_caliper_rows(log_path)
        for label in ROUND_LABELS:
            values = by_round.get(label, [])
            caliper = caliper_rows.get(label, {})
            rows.append(
                {
                    "trial": trial_index,
                    "name": label,
                    "succ": caliper.get("succ", len(values)),
                    "fail": caliper.get("fail", ""),
                    "send_rate_tps": caliper.get("send_rate_tps", ""),
                    "throughput_tps": caliper.get("throughput_tps", ""),
                    "avg_latency_ms_report": round(1000 * caliper["avg_latency_s_report"], 3) if caliper else "",
                    "avg_latency_ms_txlog": round(statistics.mean(values), 3) if values else "",
                    "p50_latency_ms": round(percentile(values, 50), 3) if values else "",
                    "p95_latency_ms": round(percentile(values, 95), 3) if values else "",
                    "p99_latency_ms": round(percentile(values, 99), 3) if values else "",
                    "min_latency_ms": round(min(values), 3) if values else "",
                    "max_latency_ms": round(max(values), 3) if values else "",
                    "source_log": log_path.name,
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = []
    for label in ROUND_LABELS:
        selected = [row for row in rows if row["name"] == label]
        summary = {"name": label, "trials": len(selected)}
        for key in [
            "succ",
            "fail",
            "send_rate_tps",
            "throughput_tps",
            "avg_latency_ms_report",
            "avg_latency_ms_txlog",
            "p50_latency_ms",
            "p95_latency_ms",
            "p99_latency_ms",
            "min_latency_ms",
            "max_latency_ms",
        ]:
            values = [float(row[key]) for row in selected if row[key] != ""]
            summary[f"{key}_mean"] = round(mean(values), 3) if values else ""
            summary[f"{key}_sd"] = round(sd(values), 3) if values else ""
        summary_rows.append(summary)

    summary_output = output.with_name(output.stem + "-summary.csv")
    with summary_output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"wrote {output} ({len(rows)} rows)")
    print(f"wrote {summary_output} ({len(summary_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
