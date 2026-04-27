# SCAPE-ZK Caliper Txlog Rerun

Date: 2026-04-27

Purpose: rerun the 15-round operation benchmark with Caliper's transaction
logging observer enabled so p50/p95/p99 latency can be audited from raw
per-transaction timestamps.

## Setup

- Network: 4-peer Fabric test network on `scapechannel`.
- Chaincode: `scapezk`, version `1.0`, sequence `1`.
- Benchmark config:
  `caliper-scapezk/benchmark-operations-txlog.yaml`.
- Transaction observer:
  `monitors.transaction: logging`.
- Trials: 10.
- Rounds per trial: 15.
- Transactions per trial: 8,000.
- Total logged transaction records: 80,000.

## Files

- `logs/caliper-operations-txlog-trial-1.log` through
  `logs/caliper-operations-txlog-trial-10.log`: raw Caliper logs containing
  `txInfo` JSON rows.
- `reports/caliper-operations-txlog-trial-1.html` through
  `reports/caliper-operations-txlog-trial-10.html`: Caliper HTML reports.
- `parse_txlog_percentiles.py`: parser used to extract Caliper table metrics
  and compute p50/p95/p99 from `time_final - time_create`.
- `caliper-operations-txlog-percentiles.csv`: per-trial metrics for all
  15 rounds.
- `caliper-operations-txlog-percentiles-summary.csv`: mean and sample standard
  deviation across the 10 trials.
- `caliper-operations-txlog-smoke.log`,
  `caliper-operations-txlog-smoke-percentiles.csv`, and the smoke HTML report:
  one preliminary validation run, not part of the 10-trial aggregate.

## Important Interpretation Note

This rerun is txlog-instrumented. Because every transaction is logged, its TPS
is lower than the earlier no-txlog Caliper run. Use this bundle to audit
percentile latency and as a separately labeled txlog-instrumented benchmark; do
not silently mix its TPS means with the earlier no-txlog Sheet 03 means.
