# Section 6 Draft: Experimental Setup And Baseline Methodology

## Experimental Setup

All experiments were conducted on a single local machine to avoid
cross-platform timing distortion between SCAPE-ZK and the compared baselines.
The benchmark host used an AMD Ryzen 5 5600X CPU, 15.6 GiB RAM, Ubuntu
24.04.4 LTS, Linux kernel 6.17.0-20-generic, Node.js v24.15.0 for the Node
benchmark stack, and Python from the local virtual environment for plotting and
 data-processing scripts. Hardware details are recorded in
[results/machine_specs.txt](/home/tomato/scape-zk/results/machine_specs.txt:1).

For SCAPE-ZK, the proving system is Groth16 via `snarkjs`, with BN254 used for
the actual Circom proof system because it remains the practical compatibility
path for the current `circomlib` EdDSA/Poseidon toolchain. The trusted setup
uses `powersOfTau28_hez_final_16.ptau` followed by one local contribution.
Inside the circuit, Poseidon is used as the hash primitive. Outside the
circuit, SHA-256 is used for general integrity-style hashing.

For same-machine cryptographic primitive benchmarking, we freeze the primitive
environment at 128-bit classical security for the pairing-friendly group layer.
Specifically, the primitive benchmark uses BLS12-381 for elliptic-curve scalar
multiplication and bilinear pairing, SHA-256 for hashing, and AES-256-GCM for
1 KB symmetric encryption. This separation is intentional: the SCAPE-ZK ZKP
implementation remains on BN254 for engineering compatibility, while the
baseline primitive calibration uses BLS12-381 to reflect a contemporary
128-bit-security pairing setting.

Workload parameters were frozen as follows: number of attributes in
`{5, 10, 20, 50}`, number of disclosed attributes in `{2, 5, 10, 20}`, batch
sizes in `{1, 10, 50, 100, 200}`, number of issuers in `{1, 5, 10}`, and
concurrent users in `{1, 10, 50, 100}`.

All micro-benchmarks were executed for 11 runs total, with the first run
dropped as warmup and the remaining 10 runs summarized as mean and standard
deviation in milliseconds. Each primitive run performs 1,000 repetitions of the
target operation to suppress timer noise. The resulting primitive means are:

- `T_hash = 0.002215 ms` for SHA-256 over 32-byte input
- `T_grp = 0.456854 ms` for BLS12-381 G1 scalar multiplication
- `T_pair = 14.724512 ms` for BLS12-381 pairing
- `T_sym = 0.005631 ms` for AES-256-GCM encryption of 1 KB

These values are recorded in
[results/primitive_microbench.csv](/home/tomato/scape-zk/results/primitive_microbench.csv:1).

## Baseline Methodology

We distinguish clearly between measured SCAPE-ZK results and baseline-derived
results.

- SCAPE-ZK values come from direct local execution of the implemented Circom,
  Groth16, CP-ABE, PRE, and BLS benchmark pipelines.
- XAuth and SSL-XIoMT retain paper-anchor values where the source papers report
  only end-to-end headline proof timings rather than a fully reproducible
  primitive decomposition.
- Scheme `[30]` is treated as a primitive-calibrated proxy model for the
  credential issue/show/verify path on the local machine, while its
  communication-reduction comparison remains paper-style.

Therefore, the baseline comparison should be described as `paper-anchored and
primitive-calibrated`, not as a complete reimplementation of every baseline
system. This wording is important for reviewer-facing accuracy.

## Reproducibility

The key commands used in the current evaluation workspace are:

```bash
npm run baseline:check
npm run bench:primitives
python3 baseline_sim.py --show-primitives
./.venv/bin/python scripts/build_modeled_table4_comparison.py
./.venv/bin/python scripts/plot_table4_computation_cost.py
MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python scripts/plot_table4_linegraphs.py
MPLCONFIGDIR=/tmp/matplotlib ./.venv/bin/python scripts/plot_matched_parameter_figures.py
```
