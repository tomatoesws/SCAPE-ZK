# Table V Computation-Cost Benchmark

Source: `SCAPE_ZK_updated.pdf`, Table V, "Authorization Verification Scalability".

This folder contains code and generated artifacts for a formula-derived computation-cost comparison aligned with the Table V scope.

Generated files:

- `table_v_cost_components.csv`
- `table_v_total_cost_vs_requests.svg`
- `table_v_cost_breakdown_100req.svg`
- `table_v_onchain_offchain_100req.svg`
- `generate_table_v_cost_graphs.py`

Primitive calibration:

- `T_zk^v`: 12.4706 ms, from `paper/results/groth16_bench.csv` request verification rows.
- `T_pair`: 31.9281 ms, from `paper/results/bls_bench.csv` `pairing_only` rows.
- `T_grp`: 5.4515 ms, derived from BLS aggregate verification residual `(verify_agg - T_pair) / n`.
- `T_hash`: 0.00044586 ms, local SHA-256 metadata-leaf calibration.

Formula mapping used:

- XAuth [6]: off-chain `n*(T_zk^v + ceil(log2 n)*T_hash)` from anonymous-proof verification plus MMHT correctness validation; on-chain `n*T_hash` from control-layer hash anchoring.
- SSL-XIoMT [8]: off-chain `n*(T_zk^v + ceil(log2 n)*T_hash)` from `ver_merkle_proof(...)` and `_ZKP_valid(...)` / `check_ZKP_validity(...)`; on-chain `n*T_hash` from Hyperledger Merkle-root anchoring.
- Scheme [30]: off-chain `n*T_zk^v + T_pair + n*T_grp` from verifier-side proof checks plus batch pairing equation (5)/(6); on-chain `n*T_hash` from blockchain authentication-record anchoring.
- SCAPE-ZK: off-chain `n*T_zk^v`; on-chain `T_pair`.

Scope note:

This estimator does not reuse the timing numbers claimed in the comparator papers. It applies the extracted formulas to a shared local primitive calibration so the graph reflects structural cost differences under one measurement basis.
