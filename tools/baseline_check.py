#!/usr/bin/env python3
"""Readiness checker for the SCAPE-ZK baseline environment.

This script verifies that the local toolchain, checked-in artifacts, and
minimal end-to-end proving flows are ready for baseline experiments.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def require_command(name: str, version_args: list[str], *, ok_returncodes: tuple[int, ...] = (0,)) -> CheckResult:
    path = shutil.which(name)
    if not path:
        return CheckResult(name, False, "missing from PATH")

    proc = run_command([name, *version_args])
    if proc.returncode not in ok_returncodes:
        detail = (proc.stderr or proc.stdout).strip() or "version check failed"
        return CheckResult(name, False, detail)

    first_line = (proc.stdout or proc.stderr).strip().splitlines()[0]
    return CheckResult(name, True, f"{path} | {first_line}")


def require_files(name: str, paths: list[str]) -> CheckResult:
    missing = [p for p in paths if not (ROOT / p).exists()]
    if missing:
        return CheckResult(name, False, f"missing: {', '.join(missing)}")
    return CheckResult(name, True, f"{len(paths)} required files present")


def command_check(
    name: str,
    args: list[str],
    *,
    cwd: Path | None = None,
    success_summary: str | None = None,
) -> CheckResult:
    proc = run_command(args, cwd=cwd)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or "command failed"
        return CheckResult(name, False, detail)

    if success_summary:
        summary = success_summary
    else:
        detail = (proc.stdout or proc.stderr).strip().splitlines()
        summary = detail[-1] if detail else "ok"
    return CheckResult(name, True, summary)


def proof_flow(
    name: str,
    witness_script: str,
    wasm: str,
    input_json: str,
    zkey: str,
    vkey: str,
) -> CheckResult:
    with tempfile.TemporaryDirectory(prefix=f"{name.lower()}_") as tmp:
        tmpdir = Path(tmp)
        witness = tmpdir / f"{name.lower()}_check.wtns"
        proof = tmpdir / f"{name.lower()}_proof.json"
        public = tmpdir / f"{name.lower()}_public.json"

        steps = [
            (
                f"{name} witness",
                [
                    "node",
                    witness_script,
                    wasm,
                    input_json,
                    str(witness),
                ],
            ),
            (
                f"{name} prove",
                [
                    "snarkjs",
                    "groth16",
                    "prove",
                    zkey,
                    str(witness),
                    str(proof),
                    str(public),
                ],
            ),
            (
                f"{name} verify",
                [
                    "snarkjs",
                    "groth16",
                    "verify",
                    vkey,
                    str(public),
                    str(proof),
                ],
            ),
        ]

        for step_name, args in steps:
            proc = run_command(args)
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout).strip() or "command failed"
                return CheckResult(name, False, f"{step_name}: {detail}")

        return CheckResult(name, True, "witness, proof, and verification succeeded")


def print_result(result: CheckResult) -> None:
    mark = "PASS" if result.ok else "FAIL"
    print(f"[{mark}] {result.name}: {result.detail}")


def main() -> int:
    results: list[CheckResult] = []

    print("SCAPE-ZK baseline readiness check")
    print("=" * 40)

    results.extend(
        [
            require_command("node", ["-v"]),
            require_command("python3", ["--version"]),
            require_command("circom", ["--version"]),
            require_command("snarkjs", ["--help"], ok_returncodes=(0, 99)),
        ]
    )

    results.append(
        require_files(
            "required artifacts",
            [
                "scripts/gen_inputs.js",
                "baseline_sim.py",
                "circuits/session_js/session.wasm",
                "circuits/request_js/request.wasm",
                "keys/session_final.zkey",
                "keys/session_vkey.json",
                "keys/request_final.zkey",
                "keys/request_vkey.json",
            ],
        )
    )

    results.append(
        command_check(
            "generate inputs",
            ["node", "scripts/gen_inputs.js"],
            success_summary="session and request inputs regenerated successfully",
        )
    )
    results.append(
        command_check(
            "baseline simulator",
            ["python3", "baseline_sim.py"],
            success_summary="all published-point validation checks passed",
        )
    )

    results.append(
        proof_flow(
            "session flow",
            "circuits/session_js/generate_witness.js",
            "circuits/session_js/session.wasm",
            "circuits/input_session.json",
            "keys/session_final.zkey",
            "keys/session_vkey.json",
        )
    )
    results.append(
        proof_flow(
            "request flow",
            "circuits/request_js/generate_witness.js",
            "circuits/request_js/request.wasm",
            "circuits/input_request.json",
            "keys/request_final.zkey",
            "keys/request_vkey.json",
        )
    )

    for result in results:
        print_result(result)

    passed = sum(1 for result in results if result.ok)
    total = len(results)
    print("-" * 40)
    print(f"Summary: {passed}/{total} checks passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
