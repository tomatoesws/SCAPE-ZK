# Table V Comparison Graph

Source: `SCAPE_ZK_updated.pdf`, Table V, "Authorization Verification Scalability".

Generated files:

- `table_v_authorization_scalability.svg`
- `table_v_primitive_calibrated_cost.csv`
- `generate_table_v_comparison.py`

Interpretation:

- This is a primitive-calibrated analytical on-chain cost comparison in milliseconds.
- It is derived from the On-chain Cost column of Table V in `SCAPE_ZK_updated.pdf` and instantiated with locally measured primitive timings from:
  - `../results/primitive_microbench.csv`
  - `../results/groth16_bench.csv`
- It is not a full protocol reimplementation of XAuth, SSL-XIoMT, or the Cross-Domain Identity Authentication Scheme for the IIoT Identification Resolution System Based on Self-Sovereign Identity [30].
- Off-chain proof-generation, encryption, and other off-chain costs are intentionally excluded.
- XAuth [6] and SSL-XIoMT [8] are modeled as `n*T_hash`.
- The Cross-Domain Identity Authentication Scheme for the IIoT Identification Resolution System Based on Self-Sovereign Identity [30] is modeled as `T_zk_verify + T_pair + n*T_grp + n*T_hash` because it includes aggregate-signature-related verification and linear group operations.
- SCAPE-ZK is modeled as `T_pair` because it verifies one aggregate authorization object on-chain.
- The IIoT SSI identity-resolution scheme should not overlap with XAuth/SSL-XIoMT in this corrected interpretation.

Measured primitive values used by the current generated CSV:

- `T_hash = 0.002215 ms`
- `T_grp = 0.456854 ms`
- `T_pair = 14.724512 ms`
- `T_zk_verify = 13.293 ms`
- Workloads: `n = {1, 10, 50, 100, 200, 1000, 5000, 10000, 20000, 50000}`.
- The `10000`-`50000` range is intended as a high-concurrency hospital or hospital-network aggregation window, not as a single clinician's interactive request count.
- Hash-only baseline crossover: `T_pair / T_hash = 6647.64`, so SCAPE-ZK becomes lower than `n*T_hash` when `n >= 6648`.

Important caveat:

- Under this primitive-calibrated model, hash-only baselines can have lower absolute cost than SCAPE-ZK at the plotted request counts because SHA-256 is much cheaper than a pairing.
- The SCAPE-ZK advantage shown by Table V is constant on-chain scaling (`O(1)`) and lower absolute primitive-calibrated cost only after the high-concurrency crossover point.

Recommended caption:

> Primitive-calibrated on-chain authorization-verification cost derived from Table V. The formulas are instantiated with locally measured SHA-256, BLS12-381 group-operation and pairing, and Groth16 verification timings. XAuth and SSL-XIoMT grow linearly with `n*T_hash`, the IIoT SSI identity-resolution scheme [30] grows linearly with additional pairing/ZKP/group-operation terms, and SCAPE-ZK remains constant because its blockchain-side verification is a single aggregate pairing check `T_pair`.

Suggested result sentence:

> As the number of authorization requests increases, SCAPE-ZK maintains constant on-chain verification cost, while XAuth, SSL-XIoMT, and the IIoT SSI identity-resolution scheme [30] grow linearly under the Table V formulas. With the measured primitives used here, SCAPE-ZK crosses below the hash-only XAuth/SSL-XIoMT model after approximately 6,648 requests and remains lower across the high-concurrency hospital-network points from `n=10000` to `n=50000`. These values are primitive-calibrated analytical costs, not full-system baseline reimplementation results.
