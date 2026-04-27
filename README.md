# SCAPE-ZK Program Artifacts

This repository contains the runnable code and evaluation files for the SCAPE-ZK
term project. SCAPE-ZK is a research prototype for privacy-preserving healthcare
data sharing. It uses zero-knowledge circuits, cryptographic benchmarks, and
Hyperledger Fabric chaincode and benchmark settings.

The repository is organized so an evaluator can review the implementation, run
basic checks, rebuild the report figures, and inspect the data used in the
paper.

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
| `SCAPE_ZK/` | LaTeX source and figures for the SCAPE-ZK paper draft. |
| `ssl_xiomt/` | Supporting SSL-XIoMT prototype files, metrics code, and figure scripts. |
| `ssl_xiomt_real_system/` | Real-system diagram and notes for the SSL-XIoMT support material. |
| `table_v_comparison/` | Corrected Table V on-chain authorization-verification comparison graph and generator. |
| `table_iv_computation_cost/` | Table IV computation-cost graph generator and outputs. |
| `table_v_computation_cost/` | Formula-derived Table V computation-cost graph generator and outputs. |
| `baselines/` | Notes and manifest describing baseline reproduction status. |
| `docs/` | Experimental setup notes and supporting writeups. |
| `tests/` | Python tests for the supporting prototype code. |
| `allcode/` | Flattened code bundle with selected scripts copied into one folder for review. |

## Prerequisites

Before running the project, make sure these tools are installed:

- Node.js 18+ and `npm`
- Python 3.10+ with `pip` and `venv`
- Go 1.20+
- `circom`
- `snarkjs`

The Fabric/Caliper experiments also need:

- Docker
- Hyperledger Fabric binaries and Docker images
- Hyperledger Caliper dependencies

The `network/` directory includes the project-specific Fabric scripts and
configuration used for the experiments. It does not include a full
`fabric-samples` checkout, runtime crypto material, `node_modules`, packaged
chaincode archives, or local binaries.

## Included Files

The main project files are stored in the structured folders above. The root also
includes `package.json`, `package-lock.json`, and `requirements.txt` for the
Node.js and Python dependencies.

Several paper PDFs, screenshots, and zipped copies of selected artifact folders
are included for reference. These files are not required for the basic checks,
but they help document the project and the evaluation material.

The nested `allcode/` folder is a flattened review bundle. It keeps many source
files in one place with filenames that show where they came from. The structured
folders should be used for normal project work.

## Installation

Clone the repository and move into it:

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

Check that the required command-line tools are available:

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
`requirements.txt`. The CSV results are already included, so these scripts do
not need to be rerun unless that part of the evaluation needs to be reproduced
from scratch.

Regenerate the main report figures from the tracked benchmark CSV files:

```sh
npm run compare:artifacts
```

This command expects the Python virtual environment at `.venv/` and writes the
figures under `results/figures/`.

Individual plotting scripts can also be run directly:

```sh
python3 scripts/plot_offchain_system_winning_graphs.py
python3 scripts/plot_proof_verification_comparison.py
python3 scripts/plot_integrity_verification_latency.py
```

## Hyperledger Fabric Assets

The chaincode implementation is here:

```text
chaincode/scape-zk/scape_zk.go
```

The local chaincode performance test is here:

```text
chaincode/scape-zk/perf_test.go
```

Fabric network and Caliper configuration snapshots are under:

```text
network/fabric-test-network/
network/scripts/
```

These files document the setup used for the blockchain-layer experiments. To
rerun the full Fabric/Caliper experiment on a new machine, install Fabric and
Caliper first, then place or adapt these files inside a working Fabric
test-network environment.

## Report Figures And Data

Result data is stored under `results/`. The main generated figures are:

- `results/figures/offchain_system/02_authorization_preparation_cost.png`
- `results/figures/offchain_system/03_cross_domain_delegation_latency.png`
- `results/figures/proof_verification_latency.pdf`
- `results/figures/integrity_verification_latency.pdf`
- `table_v_comparison/table_v_authorization_scalability.svg`
- `table_v_computation_cost/table_v_total_cost_vs_requests.svg`
- `table_v_computation_cost/table_v_cost_breakdown_100req.svg`
- `table_v_computation_cost/table_v_onchain_offchain_100req.svg`

The repeated blockchain-layer Caliper benchmark bundle is stored here:

```text
results/blockchain/scapezk-caliper-repeated-2026-04-22/
```

It includes raw and summary CSVs, generated figures, figure scripts, workbook
files, and draft/audit notes. Some Caliper logs and HTML reports are also kept
inside the categorized experiment bundle for traceability.

## Scope Notes

This repository contains the SCAPE-ZK prototype code, benchmark scripts, and
figure-generation files used for the term project. It is not a production
application, and it does not include full implementations of every baseline
paper. Baseline status and limits are documented in `baselines/README.md`.

The Fabric `VerifyProof` benchmark is a blockchain-layer transaction benchmark.
It records proof-verification and authorization results as ledger operations. It
does not run full Groth16 or BLS proof verification inside Fabric chaincode.

## Troubleshooting

If `npm test` fails because a package such as `circomlibjs` is missing, run:

```sh
npm install
```

If the Python plotting scripts fail because modules are missing, activate the
virtual environment and install the plotting dependencies:

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

If Fabric scripts fail, check that Docker, Fabric binaries, Fabric images, and
Caliper dependencies are installed and available on `PATH`.
