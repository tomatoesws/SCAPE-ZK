# SCAPE-ZK

This repository currently contains the baseline evaluation toolkit for the
SCAPE-ZK prototype: Circom circuits, proving artifacts, benchmark scripts, and
paper-alignment simulators.

## Current Status

The cryptographic toolchain is usable for baseline experiments:

- Node.js dependencies are installed for `snarkjs`, `circomlib`, and `circomlibjs`
- `circom` and `snarkjs` are available locally
- sample inputs can be generated
- the session and request circuits can complete witness, proof, and verify flows
- the paper baseline simulator passes its published-point validation checks

What is not here yet is a full application/service layer. This repo is still a
research and evaluation workspace, now with a repeatable readiness check.

## Quick Start

Run the full readiness check:

```bash
npm run baseline:check
```

Run the individual pieces:

```bash
npm run gen:inputs
npm run sim:baseline
npm run bench:primitives
```

Regenerate the primitive-calibrated comparison artifacts:

```bash
npm run compare:artifacts
```

## What `baseline:check` Verifies

- required binaries are on `PATH`: `node`, `python3`, `circom`, `snarkjs`
- required proving artifacts exist
- `scripts/gen_inputs.js` produces consistent circuit inputs
- `baseline_sim.py` passes all baseline validation checks
- the session circuit completes witness generation, Groth16 proving, and verification
- the request circuit completes witness generation, Groth16 proving, and verification

## Comparison Methodology

This repository now separates:

- `measured SCAPE-ZK results`: direct local benchmark outputs
- `paper-anchored baseline values`: headline numbers preserved from source papers
- `primitive-calibrated baseline proxies`: formulas instantiated with the local
  primitive micro-benchmarks in [results/primitive_microbench.csv](/home/tomato/scape-zk/results/primitive_microbench.csv:1)

That means the current baseline comparison is best described as
`paper-anchored and primitive-calibrated`, not as a full reimplementation of
all compared schemes.

The main outputs for the paper are:

- [results/table4_modeled_comparison.csv](/home/tomato/scape-zk/results/table4_modeled_comparison.csv:1)
- [results/table4_computation_cost_summary.csv](/home/tomato/scape-zk/results/table4_computation_cost_summary.csv:1)
- [results/figures/table4_computation_cost.png](/home/tomato/scape-zk/results/figures/table4_computation_cost.png)
- [results/figures/table4_linegraphs_paperstyle.png](/home/tomato/scape-zk/results/figures/table4_linegraphs_paperstyle.png)
- [results/figures/matched_proof_cost.png](/home/tomato/scape-zk/results/figures/matched_proof_cost.png)
- [results/figures/matched_verification_cost.png](/home/tomato/scape-zk/results/figures/matched_verification_cost.png)
