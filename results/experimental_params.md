# Frozen Experimental Parameters

## Cryptographic parameters
- **ZKP system**: Groth16 via snarkjs
- **Curve (ZKP)**: BN254 (alt_bn128 / bn-128)
- **Pairing / primitive micro-benchmark curve**: BLS12-381
- **Hash (in-circuit)**: Poseidon (circomlib)
- **Hash (out-of-circuit)**: SHA-256
- **Symmetric cipher**: AES-256-GCM
- **Security level**: BN254 for the deployed Groth16 path; 128-bit for the primitive-calibrated pairing layer
- **Trusted setup**: powersOfTau28_hez_final_16.ptau (Hermez ceremony) + 1 local contribution

## Rationale for BN254
SCAPE-ZK's actual Groth16 implementation remains on BN254 because it is the
practical compatibility path for the current Circom and circomlib stack.
Primitive micro-benchmarking is separately performed on BLS12-381 so that the
same-machine baseline calibration can be stated against a contemporary 128-bit
pairing setting.

## Workload parameters
- Session circuit: 11,705 R1CS constraints, 10 attributes, 6 public inputs
- Request circuit: 1,440 R1CS constraints, 2 public inputs
- Attributes swept: {5, 10, 20, 50}
- Disclosed attributes: {2, 5, 10, 20}
- Batch sizes (BLS aggregate / verification): {1, 10, 50, 100, 200}
- Issuers: {1, 5, 10}
- Concurrent users: {1, 10, 50, 100}

## System parameters
- Hardware: single machine for all benchmarks, recorded in `results/machine_specs.txt`
- Plotting and data processing: local Python virtualenv `./.venv`
- Primitive micro-benchmarking: Node.js benchmark script on the same host
- Fabric / IPFS architecture notes: document in the paper as target deployment assumptions, not local benchmarked subsystems unless explicitly reproduced

## Measurement methodology
- Primitive micro-benchmarking: 11 total runs, first run dropped, 1,000 ops per run
- All other benchmarks: ≥10 runs per measurement, warmup runs dropped where applicable
- Report mean ± standard deviation
- Time in milliseconds
- Primary primitive outputs:
  - `T_hash = 0.002215 ms`
  - `T_grp = 0.456854 ms`
  - `T_pair = 14.724512 ms`
  - `T_sym = 0.005631 ms`
- Source files:
  - `results/primitive_microbench.csv`
  - `results/cross_scheme_modeled_computation_comparison.csv`
  - `results/cross_scheme_computation_cost_summary.csv`
