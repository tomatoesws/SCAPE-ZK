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
