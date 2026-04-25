# Table V Comparison Graph

Source: `SCAPE_ZK_updated.pdf`, Table V, "Authorization Verification Scalability".

Generated files:

- `table_v_authorization_scalability.svg`
- `table_v_normalized_cost.csv`
- `generate_table_v_comparison.py`

Interpretation:

- This is a normalized analytical on-chain cost comparison, not measured runtime.
- It is derived from the On-chain Cost column of Table V in `SCAPE_ZK_updated.pdf`.
- Off-chain proof-generation, encryption, and other off-chain costs are intentionally excluded.
- XAuth [6] and SSL-XIoMT [8] are modeled as `n*T_hash`.
- Scheme [30] is modeled as `T_zk_verify + T_pair + n*T_grp + n*T_hash` because it includes aggregate-signature-related verification and linear group operations.
- SCAPE-ZK is modeled as `T_pair` because it verifies one aggregate authorization object on-chain.
- Scheme [30] should not overlap with XAuth/SSL-XIoMT in this corrected interpretation.

Recommended caption:

> Normalized on-chain authorization-verification scalability derived from the corrected Table V interpretation. XAuth and SSL-XIoMT grow linearly with `n*T_hash`. Scheme [30] also grows linearly but with higher cost because its on-chain verification includes aggregate-signature-related pairing/ZKP verification and linear group operations. SCAPE-ZK remains constant because its blockchain-side verification is a single aggregate pairing check `T_pair`.

Suggested result sentence:

> As the number of authorization requests increases, SCAPE-ZK maintains constant on-chain verification cost, XAuth and SSL-XIoMT increase linearly with hash/check work, and Scheme [30] increases linearly at a higher cost due to additional aggregate-signature and group-operation verification. This demonstrates that SCAPE-ZK achieves superior on-chain authorization scalability under high-concurrency EHR sharing.
