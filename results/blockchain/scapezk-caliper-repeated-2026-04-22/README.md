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
figure generator, paper draft text, and generated SVG figures. Trial logs and
HTML reports are intentionally omitted to keep the repository small.

Artifacts:

- Raw per-trial CSV: `caliper-operations-repeated-raw.csv`
- Aggregate CSV: `caliper-operations-repeated-summary.csv`
- Section 7.C/7.D draft text: `draft/section_7c_7d_draft.md`
- Figure generator: `scripts/generate_repeated_figures.py`
- Generated SVG figures:
  - `figures/repeated-throughput-1000tx.svg`
  - `figures/repeated-latency-1000tx.svg`
  - `figures/repeated-throughput-by-load.svg`
  - `figures/repeated-success-summary.svg`

All ten logged trials completed 15/15 rounds. Total failed transactions across parsed rounds: 0.

## Aggregate Results

| Round | Trials | Success | Fail | Throughput TPS mean +/- SD | Avg latency s mean +/- SD | Throughput range |
|---|---:|---:|---:|---:|---:|---:|
| recordexists-100tx | 10 | 1000 | 0 | 112.98 +/- 1.41 | 0.009 +/- 0.003 | 110.7-114.7 |
| recordexists-500tx | 10 | 5000 | 0 | 447.05 +/- 15.10 | 0.010 +/- 0.000 | 425.5-470.8 |
| recordexists-1000tx | 10 | 10000 | 0 | 702.38 +/- 38.86 | 0.010 +/- 0.000 | 657.0-770.4 |
| register-100tx | 10 | 1000 | 0 | 19.34 +/- 3.26 | 0.276 +/- 0.064 | 10.3-21.4 |
| register-500tx | 10 | 5000 | 0 | 131.33 +/- 2.51 | 0.095 +/- 0.007 | 128.9-136.4 |
| register-1000tx | 10 | 10000 | 0 | 215.15 +/- 14.24 | 0.089 +/- 0.012 | 195.5-243.7 |
| revoke-100tx | 10 | 1000 | 0 | 19.87 +/- 3.03 | 0.266 +/- 0.061 | 11.5-21.6 |
| revoke-500tx | 10 | 5000 | 0 | 130.83 +/- 4.76 | 0.086 +/- 0.008 | 120.7-138.3 |
| revoke-1000tx | 10 | 10000 | 0 | 221.20 +/- 13.61 | 0.086 +/- 0.008 | 202.7-249.8 |
| updatecred-100tx | 10 | 1000 | 0 | 20.28 +/- 1.49 | 0.262 +/- 0.030 | 17.4-22.0 |
| updatecred-500tx | 10 | 5000 | 0 | 131.65 +/- 5.06 | 0.084 +/- 0.005 | 125.0-138.7 |
| updatecred-1000tx | 10 | 10000 | 0 | 221.56 +/- 10.47 | 0.092 +/- 0.008 | 196.7-232.0 |
| verifyproof-100tx | 10 | 1000 | 0 | 20.07 +/- 3.30 | 0.266 +/- 0.049 | 11.8-24.2 |
| verifyproof-500tx | 10 | 5000 | 0 | 130.99 +/- 4.93 | 0.082 +/- 0.004 | 121.5-137.3 |
| verifyproof-1000tx | 10 | 10000 | 0 | 221.19 +/- 8.03 | 0.087 +/- 0.007 | 205.3-231.1 |

## 1000-Transaction Rounds

| Operation | Throughput TPS mean +/- SD | Avg latency s mean +/- SD | Failures |
|---|---:|---:|---:|
| recordexists | 702.38 +/- 38.86 | 0.010 +/- 0.000 | 0 |
| register | 215.15 +/- 14.24 | 0.089 +/- 0.012 | 0 |
| revoke | 221.20 +/- 13.61 | 0.086 +/- 0.008 | 0 |
| updatecred | 221.56 +/- 10.47 | 0.092 +/- 0.008 | 0 |
| verifyproof | 221.19 +/- 8.03 | 0.087 +/- 0.007 | 0 |

Note: SD is sample standard deviation across the ten logged Caliper trials, not per-transaction latency dispersion.
