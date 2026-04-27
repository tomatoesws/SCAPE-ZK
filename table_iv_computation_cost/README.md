# Table IV Computation-Cost Benchmark Graphs

Source: `SCAPE_ZK_updated.pdf`, Table IV.

This folder contains code and generated artifacts for the computation-cost comparison of only the schemes and columns shown in Table IV:

- XAuth [6]
- SSL-XIoMT [8]
- Scheme [30]
- SCAPE-ZK

Table IV columns covered:

- `Proof Gen`
- `Amortized Proof`
- `Encrypt`
- `Proof Ver`
- `Integrity & Delegation Verification`

Generated files:

- `generate_table_iv_cost_graphs.py`
- `table_iv_primitive_benchmarks.csv`
- `table_iv_cost_components.csv`
- `table_iv_total_cost_vs_requests.svg`
- `table_iv_component_breakdown.svg`
- `table_iv_columns_at_n.svg`

Run:

```bash
python3 paper/table_iv_computation_cost/generate_table_iv_cost_graphs.py
```

Useful options:

```bash
python3 paper/table_iv_computation_cost/generate_table_iv_cost_graphs.py --attrs 50 --breakdown-n 50
```

Notes:

- Setup is not plotted as a separate phase because setup is not a Table IV column in `SCAPE_ZK_updated.pdf`; this keeps the comparison restricted to the table.
- Baseline schemes are not fully reimplemented. The script uses local SCAPE-ZK primitive measurements and calibrated primitive proxies to instantiate the symbolic Table IV terms.
- `T_merk* + T_hash^ell + T_pre^v` is used for SCAPE-ZK's updated integrity/delegation term.
- The SVGs should be treated as experiment-backed Table-IV cost estimates, not as direct published-runtime reproductions of XAuth, SSL-XIoMT, or Scheme [30].

