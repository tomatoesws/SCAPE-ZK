
# SCAPE-ZK

SCAPE-ZK is a research prototype and evaluation workspace for a privacy-
preserving healthcare data-sharing design built with Circom, Groth16, and
supporting benchmark scripts. This repository contains:

- Circom circuits and proving artifacts for the SCAPE-ZK flow
- benchmark scripts for local measurements
- plotting scripts used for the report figures
- generated CSV and figure outputs under [results](/home/tomato/scape-zk/results)

This README is written so another student, lecturer, or evaluator can install,
run, and test the project without needing extra context.

## Repository Structure

- [circuits](/home/tomato/scape-zk/circuits): Circom circuits, generated WASM, and witness helpers
- [keys](/home/tomato/scape-zk/keys): proving and verification keys
- [scripts](/home/tomato/scape-zk/scripts): benchmark, plotting, and artifact-generation scripts
- [tools](/home/tomato/scape-zk/tools): reproducibility and readiness checks
- [results](/home/tomato/scape-zk/results): generated tables, CSV files, and figures
- [baselines](/home/tomato/scape-zk/baselines): notes about baseline reproduction status
- [docs](/home/tomato/scape-zk/docs): experiment setup and supporting writeups

## What This Project Runs

The repository supports three main tasks:

1. Generate SCAPE-ZK sample inputs for the Circom circuits.
2. Run local benchmark and plotting scripts for the report figures.
3. Verify that the checked-in proving artifacts can complete witness
   generation, proof generation, and proof verification end to end.

This is not a full web application. It is an experiment and evaluation codebase.

## Prerequisites

Install these tools before running the project:

- `Node.js` 18+ and `npm`
- `Python` 3.10+ with `pip` and `venv`
- `circom`
- `snarkjs`

The repository already includes generated circuit artifacts such as:

- `circuits/session_js/session.wasm`
- `circuits/request_js/request.wasm`
- `keys/session_final.zkey`
- `keys/request_final.zkey`

So you do not need to rebuild the trusted setup to run the main checks.

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd scape-zk
```

### 2. Install Node.js dependencies

```bash
npm install
```

This installs the JavaScript dependencies used by the circuit input generator
and `snarkjs`-based workflow.

### 3. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Python plotting/data packages

```bash
pip install matplotlib numpy pandas
```

These packages are needed for the comparison and plotting scripts.

### 5. Install `circom` and make sure `snarkjs` is on `PATH`

Verify the required CLI tools:

```bash
node -v
python3 --version
circom --version
snarkjs --help
```

If `snarkjs` is not globally available, you can use the local copy via:

```bash
npx snarkjs --help
```

If your environment does not expose the local binary automatically, add:

```bash
export PATH="$PWD/node_modules/.bin:$PATH"
```

## How To Run The Project

### Option A: Run the main components separately

Generate fresh circuit inputs:

```bash
npm run gen:inputs
```

Run primitive micro-benchmarks:

```bash
npm run bench:primitives
```

### Option B: Regenerate report figures

Activate the Python virtual environment first, then run:

```bash
npm run compare:artifacts
```

This regenerates the active figure outputs and supporting CSV tables inside
[results](/home/tomato/scape-zk/results) and
[results/figures](/home/tomato/scape-zk/results/figures).

## How To Test The Program

For a quick local smoke test, run:

```bash
npm test
```

This command regenerates the sample circuit inputs.

For figure generation, run:

```bash
npm run compare:artifacts
```

## Figures Used In The Report

The main figures currently used in the report are:

- [Off-Chain Authorization Preparation Cost](/home/tomato/scape-zk/results/figures/offchain_system/02_authorization_preparation_cost.pdf)
- [Proof Verification Latency](/home/tomato/scape-zk/results/figures/proof_verification_latency.pdf)
- [Integrity Verification Latency](/home/tomato/scape-zk/results/figures/integrity_verification_latency.pdf)
- [Delegation Latency](/home/tomato/scape-zk/results/figures/offchain_system/03_cross_domain_delegation_latency.pdf)

The plotting scripts kept for the report figures are:

- `scripts/plot_offchain_system_winning_graphs.py`: off-chain authorization and delegation cost
- `scripts/plot_proof_verification_comparison.py`: proof verification latency
- `scripts/plot_integrity_verification_latency.py`: integrity verification latency

## Troubleshooting

### `circom: command not found`

Install `circom` and ensure it is available on your shell `PATH`.

### `snarkjs: command not found`

Use the local binary with `npx snarkjs`, or export:

```bash
export PATH="$PWD/node_modules/.bin:$PATH"
```

### Python plotting scripts fail with missing modules

Make sure the virtual environment is activated and install:

```bash
pip install matplotlib numpy pandas
```

### The readiness check does not reach `9/9 checks passed`

Recheck:

- Node.js is installed
- Python 3 is installed
- `circom` is installed
- `snarkjs` is available
- the checked-in files under `circuits/` and `keys/` are present

## Current Scope Note

This repository includes working SCAPE-ZK experiments and active figure
generation code. It does not yet contain full, faithful reproductions of all
baseline systems discussed in the report. Historical reproduction status is documented in
[baselines/README.md](/home/tomato/scape-zk/baselines/README.md:1).
=======
# SCAPE-ZK Program Artifacts

This repository contains the runnable program assets for the SCAPE-ZK project:
zero-knowledge circuits and benchmarks, BLS/CP-ABE benchmark scripts,
Hyperledger Fabric chaincode, and Fabric network experiment configuration.

## Layout

| Path | Contents |
| --- | --- |
| `circuits/` | Circom circuits, sample inputs, generated witnesses, R1CS files, and WASM witness calculators. |
| `scripts/` | Benchmark and plotting scripts for Groth16, BLS, CP-ABE, and attribute sweeps. |
| `keys/` | Verification keys used by the local circuit benchmark flow. |
| `chaincode/scape-zk/` | Go chaincode and local performance tests for SCAPE-ZK ledger operations. |
| `network/` | Fabric setup scripts, 4-peer test-network scripts, compose overlays, cryptogen configs, and Caliper configs. |
| `results/` | Existing benchmark result data and figures already tracked in this repo. |

## JavaScript/Circom Benchmarks

Install the Node.js dependencies from the repository root:

```sh
npm install
```

Run individual scripts from `scripts/`, for example:

```sh
node scripts/bench_bls.js
node scripts/bench_snarkjs.js
python3 scripts/bench_cpabe.py
```

## Chaincode

The Fabric chaincode lives in `chaincode/scape-zk/`.

```sh
cd chaincode/scape-zk
go test ./...
```

## Fabric Network Assets

The `network/` directory stores only project-specific scripts/configuration.
It does not vendor the full `fabric-samples` checkout, generated crypto
material, node modules, packaged chaincode archives, or local binaries.
>>>>>>> origin/main
