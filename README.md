# SCAPE-ZK Program Artifacts

This repository contains the runnable program assets and evaluation artifacts for
the SCAPE-ZK term project. It is a research prototype for privacy-preserving
healthcare data sharing using zero-knowledge circuits, cryptographic
microbenchmarks, and Hyperledger Fabric chaincode/benchmark configuration.

The repository is intended to let an evaluator inspect the implementation,
rerun the lightweight checks, regenerate report figures, and review the
experimental data used in the paper.

## Repository Layout

| Path | Contents |
| --- | --- |
| `circuits/` | Circom circuits, sample inputs, generated witnesses, R1CS files, and WASM witness calculators. |
| `keys/` | Verification keys used by the local circuit benchmark flow. |
| `scripts/` | Benchmark, input-generation, and plotting scripts for Groth16, BLS, CP-ABE, PRE, Merkle, and report figures. |
| `chaincode/scape-zk/` | Go chaincode and local performance tests for SCAPE-ZK ledger operations. |
| `network/` | Project-specific Fabric setup scripts, 4-peer test-network assets, compose overlays, cryptogen configs, and Caliper configs. |
| `results/` | Existing benchmark CSV/JSON data and generated report figures. |
| `results/blockchain/` | Compact repeated Caliper benchmark bundle for the blockchain-layer evaluation. |
| `table_v_comparison/` | Corrected Table V on-chain authorization-verification comparison graph and generator. |
| `table_v_computation_cost/` | Formula-derived Table V computation-cost graph generator and outputs. |
| `baselines/` | Notes and manifest describing baseline reproduction status. |
| `docs/` | Experimental setup notes and supporting writeups. |

## Prerequisites

Install these tools before running the project:

- Node.js 18+ and `npm`
- Python 3.10+ with `pip` and `venv`
- Go 1.20+
- `circom`
- `snarkjs`

Fabric/Caliper experiments additionally require:

- Docker
- Hyperledger Fabric binaries and Docker images
- Hyperledger Caliper dependencies

The `network/` directory stores project-specific Fabric scripts and
configuration. It does not vendor a complete `fabric-samples` checkout, runtime
crypto material, `node_modules`, packaged chaincode archives, or local binaries.

## Installation

Clone the repository and enter it:

```sh
git clone <repository-url>
cd paper
```

Install Node.js dependencies:

```sh
npm install
```

Create and activate a Python virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify command-line tools:

```sh
node -v
npm -v
python3 --version
go version
circom --version
npx snarkjs --help
```

## Quick Checks

Run the JavaScript/Circom input-generation smoke test:

```sh
npm test
```

Run the Go chaincode tests:

```sh
cd chaincode/scape-zk
go test ./...
cd ../..
```

Regenerate the corrected Table V on-chain authorization graph:

```sh
python3 table_v_comparison/generate_table_v_comparison.py
```

Regenerate the Table V computation-cost graphs:

```sh
python3 table_v_computation_cost/generate_table_v_cost_graphs.py
```

## Benchmark And Figure Commands

Generate fresh circuit input JSON files:

```sh
npm run gen:inputs
```

Run primitive JavaScript microbenchmarks:

```sh
npm run bench:primitives
```

Some optional Python crypto benchmark scripts, such as `scripts/bench_cpabe.py`
and `scripts/bench_pre.py`, require Charm-Crypto in addition to
`requirements.txt`. The tracked CSV results can be used without rerunning those
optional scripts.

Regenerate the main report figures from the tracked benchmark CSV files:

```sh
npm run compare:artifacts
```

This command expects the Python virtual environment at `.venv/` and writes
figure outputs under `results/figures/`.

Individual plotting scripts can also be run directly:

```sh
python3 scripts/plot_offchain_system_winning_graphs.py
python3 scripts/plot_proof_verification_comparison.py
python3 scripts/plot_integrity_verification_latency.py
```

## Hyperledger Fabric Assets

The chaincode implementation is in:

```text
chaincode/scape-zk/scape_zk.go
```

The local chaincode performance test is:

```text
chaincode/scape-zk/perf_test.go
```

Fabric network and Caliper configuration snapshots are under:

```text
network/fabric-test-network/
network/scripts/
```

These files document the project-specific setup used for the blockchain-layer
experiments. To rerun the full Fabric/Caliper experiment on a new machine, first
install Fabric and Caliper, then place or adapt these assets inside a working
Fabric test-network environment.

## Report Figures And Data

Tracked result data is stored under `results/`. Main generated figures include:

- `results/figures/offchain_system/02_authorization_preparation_cost.png`
- `results/figures/offchain_system/03_cross_domain_delegation_latency.png`
- `results/figures/proof_verification_latency.pdf`
- `results/figures/integrity_verification_latency.pdf`
- `table_v_comparison/table_v_authorization_scalability.svg`
- `table_v_computation_cost/table_v_total_cost_vs_requests.svg`
- `table_v_computation_cost/table_v_cost_breakdown_100req.svg`
- `table_v_computation_cost/table_v_onchain_offchain_100req.svg`

The repeated blockchain-layer Caliper benchmark bundle is stored at:

```text
results/blockchain/scapezk-caliper-repeated-2026-04-22/
```

It includes the raw and aggregate CSVs, four generated SVG figures, the figure
generator, and the Section 7.C/7.D draft text. Trial logs and HTML reports are
omitted from this compact repository copy.

## Scope Notes

This repository contains the SCAPE-ZK prototype code, benchmark scripts, and
figure-generation artifacts used for the term project. It is not a production
application and does not provide full faithful implementations of every baseline
paper. Baseline status and limitations are documented in `baselines/README.md`.

The Fabric `VerifyProof` benchmark is a blockchain-layer transaction benchmark.
It records proof-verification/authorization results as ledger operations; it
does not perform full Groth16 or BLS proof verification inside Fabric chaincode.

## Troubleshooting

If `npm test` fails with a missing package such as `circomlibjs`, run:

```sh
npm install
```

If Python plotting scripts fail with missing modules, activate the virtual
environment and install the plotting dependencies:

```sh
source .venv/bin/activate
pip install -r requirements.txt
```

On Debian/Ubuntu, if `python3 -m venv .venv` reports that `ensurepip` is not
available, install the OS venv/pip packages first:

```sh
sudo apt install python3-venv python3-pip
```

If `snarkjs` is not globally available, use the local dependency through `npx`:

```sh
npx snarkjs --help
```

If Fabric scripts fail, verify Docker, Fabric binaries, Fabric images, and
Caliper dependencies are installed and available on `PATH`.
