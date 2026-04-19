# Frozen Experimental Parameters (Member A scope)

## Cryptographic parameters
- **ZKP system**: Groth16 via snarkjs
- **Curve (ZKP)**: BN254 (alt_bn128 / bn-128)
- **Curve (BLS signatures)**: BLS12-381 (Member C dependency)
- **Hash (in-circuit)**: Poseidon (circomlib)
- **Hash (out-of-circuit)**: SHA-256
- **Security level**: ~100-bit ZKP (post-Kim-Barbulescu) / 128-bit BLS (composite)
- **Trusted setup**: powersOfTau28_hez_final_16.ptau (Hermez ceremony) + 1 local contribution

## Rationale for BN254
Consistent with circom/snarkjs ecosystem and baseline implementations
(XAuth [6], SSL-XIoMT [8] both use BN254-compatible primitives).
BLS12-381 ZKP instantiation tested and deferred to extended version
due to circomlib EdDSA incompatibility with BLS12-381 scalar field.

## Circuit parameters (Member A)
- Session circuit: 11,705 R1CS constraints, 10 attributes, 6 public inputs
- Request circuit: 1,440 R1CS constraints, 2 public inputs
- Attributes swept: {5, 10, 20, 50} — TBD in Day 3
- Batch sizes (BLS aggregate): {1, 10, 50, 100, 200} — TBD in Day 3

## Measurement methodology
- ≥10 runs per measurement, warmup runs dropped
- Report mean ± standard deviation
- Time in milliseconds
- Hardware: see machine_specs.txt
