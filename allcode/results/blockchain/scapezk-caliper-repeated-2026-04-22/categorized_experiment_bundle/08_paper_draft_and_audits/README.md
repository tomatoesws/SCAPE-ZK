# SCAPE-ZK Repeated Caliper Operation Trials

Date: 2026-04-22

Scope: ten logged Caliper trials of `caliper-scapezk/benchmark-operations.yaml` on the 4-peer Fabric network. The warm-up run was excluded from statistics.

Command shape:

```bash
npx caliper launch manager \
  --caliper-workspace ./caliper-scapezk \
  --caliper-benchconfig benchmark-operations.yaml \
  --caliper-networkconfig network.yaml \
  --caliper-flow-only-test
```

This directory is the compact submission bundle. It keeps the parsed CSV data,
figure generator, paper draft text, workbook audit patch, and generated figures. Trial logs and
HTML reports are intentionally omitted to keep the repository small.

Artifacts:

- Raw per-trial CSV: `caliper-operations-repeated-raw.csv`
- Aggregate CSV: `caliper-operations-repeated-summary.csv`
- Master-results import CSV: `blockchain_tps_sheet03_import.csv`
- Master-results workbook patch: `SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_populated.xlsx`
- Workbook audit note: `WORKBOOK_AUDIT_FIX.md`
- Section 7.C/7.D draft text: `draft/section_7c_7d_draft.md`
- Figure generator: `scripts/generate_repeated_figures.py`
- Locked Day-6 Section 7.C figure:
  - `figures/fig_fabric_tps_vs_load.png`
  - `figures/fig_fabric_tps_vs_load.pdf`
- Supplemental generated SVG figures:
  - `figures/repeated-throughput-1000tx.svg`
  - `figures/repeated-latency-1000tx.svg`
  - `figures/repeated-throughput-by-load.svg`
  - `figures/repeated-success-summary.svg`

All ten logged trials completed 15/15 rounds. Total failed transactions across parsed rounds: 0.

`blockchain_tps_sheet03_import.csv` is a workbook-facing extract for the
`03_Blockchain_TPS` audit sheet. It reports latency in milliseconds, marks
`Register`, `VerifyProof`, `Revoke`, and `UpdateCred` as included in the locked
write-operation template, and marks `RecordExists` as a separate read-only query.
`SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_populated.xlsx` is a populated
single-sheet workbook patch for the real master workbook, which was not present
in this workspace.

## Aggregate Results

| Round | Trials | Success | Fail | Throughput TPS mean +/- SD | Avg latency ms mean +/- SD | Throughput range |
|---|---:|---:|---:|---:|---:|---:|
| recordexists-100tx | 10 | 1000 | 0 | 112.98 +/- 1.41 | 9 +/- 3 | 110.7-114.7 |
| recordexists-500tx | 10 | 5000 | 0 | 447.05 +/- 15.10 | 10 +/- 0 | 425.5-470.8 |
| recordexists-1000tx | 10 | 10000 | 0 | 702.38 +/- 38.86 | 10 +/- 0 | 657.0-770.4 |
| register-100tx | 10 | 1000 | 0 | 19.34 +/- 3.26 | 276 +/- 64 | 10.3-21.4 |
| register-500tx | 10 | 5000 | 0 | 131.33 +/- 2.51 | 95 +/- 7 | 128.9-136.4 |
| register-1000tx | 10 | 10000 | 0 | 215.15 +/- 14.24 | 89 +/- 12 | 195.5-243.7 |
| revoke-100tx | 10 | 1000 | 0 | 19.87 +/- 3.03 | 266 +/- 61 | 11.5-21.6 |
| revoke-500tx | 10 | 5000 | 0 | 130.83 +/- 4.76 | 86 +/- 8 | 120.7-138.3 |
| revoke-1000tx | 10 | 10000 | 0 | 221.20 +/- 13.61 | 86 +/- 8 | 202.7-249.8 |
| updatecred-100tx | 10 | 1000 | 0 | 20.28 +/- 1.49 | 262 +/- 30 | 17.4-22.0 |
| updatecred-500tx | 10 | 5000 | 0 | 131.65 +/- 5.06 | 84 +/- 5 | 125.0-138.7 |
| updatecred-1000tx | 10 | 10000 | 0 | 221.56 +/- 10.47 | 92 +/- 8 | 196.7-232.0 |
| verifyproof-100tx | 10 | 1000 | 0 | 20.07 +/- 3.30 | 266 +/- 49 | 11.8-24.2 |
| verifyproof-500tx | 10 | 5000 | 0 | 130.99 +/- 4.93 | 82 +/- 4 | 121.5-137.3 |
| verifyproof-1000tx | 10 | 10000 | 0 | 221.19 +/- 8.03 | 87 +/- 7 | 205.3-231.1 |

## 1000-Transaction Rounds

| Operation | Throughput TPS mean +/- SD | Avg latency ms mean +/- SD | Failures |
|---|---:|---:|---:|
| recordexists | 702.38 +/- 38.86 | 10 +/- 0 | 0 |
| register | 215.15 +/- 14.24 | 89 +/- 12 | 0 |
| revoke | 221.20 +/- 13.61 | 86 +/- 8 | 0 |
| updatecred | 221.56 +/- 10.47 | 92 +/- 8 | 0 |
| verifyproof | 221.19 +/- 8.03 | 87 +/- 7 | 0 |

Note: SD is sample standard deviation across the ten logged Caliper trials, not per-transaction latency dispersion.
