# SCAPE-ZK Blockchain Experiment Bundle

This bundle collects the files used to run, process, audit, and write up the
SCAPE-ZK Hyperledger Fabric repeated Caliper experiment.

The main experiment is the ten-trial no-txlog Caliper benchmark of
`benchmark-operations.yaml` on the 4-peer Fabric network. The txlog rerun is
included only as auxiliary audit data for percentile latency.

## Folder Layout

| Folder | Purpose |
|---|---|
| `01_run_commands_and_network/` | Fabric test-network setup scripts and network configuration files. |
| `02_chaincode/` | SCAPE-ZK Go chaincode and Go module files used for deployment. |
| `03_caliper_workload/` | Caliper benchmark YAML files and workload JavaScript files. |
| `04_raw_caliper_results/` | Primary raw no-txlog results: raw CSV, 10 trial logs, 10 trial HTML reports, and excluded warm-up report. |
| `05_processed_results/` | Processed summary CSV and workbook import CSV files. |
| `06_figures/` | Generated figures used for paper/reporting. |
| `07_workbooks/` | Workbook patches and the v13 master workbook copy. |
| `08_paper_draft_and_audits/` | Section draft, README, and audit/feedback notes. |
| `09_reproduction_scripts/` | Python scripts used to generate figures and audit workbook imports. |
| `10_txlog_auxiliary/` | Txlog-instrumented rerun files for percentile latency audit only. |
| `11_generated_fabric_identities_and_deploy_script/` | Local-only generated Fabric MSP/TLS identity files and chaincode deployment script. This folder is intentionally ignored for GitHub because it contains private keys. |

## Start Here

- For the paper text: `08_paper_draft_and_audits/section_7c_7d_draft.md`
- For raw measured data: `04_raw_caliper_results/caliper-operations-repeated-raw.csv`
- For aggregate paper values: `05_processed_results/caliper-operations-repeated-summary.csv`
- For the main graph: `06_figures/fig_fabric_tps_vs_load.png`
- For provenance details: `MANIFEST.md`

## Data Boundary

Use the no-txlog files in `04_raw_caliper_results/` and
`05_processed_results/` for the main TPS and average-latency claims.

Use `10_txlog_auxiliary/` only for percentile latency audit columns. Do not use
txlog throughput to replace the main TPS values, because transaction logging
adds measurement overhead.

This bundle does not contain equivalent Fabric/Caliper deployments for XAuth,
SSL-XIoMT, or the IIoT SSI identity-resolution scheme. Therefore, it must not be
used to claim direct baseline TPS comparisons.

## Security Note

`11_generated_fabric_identities_and_deploy_script/` includes generated Fabric
MSP/TLS private keys referenced by the Caliper network configuration. It is
listed in this README for local provenance, but the bundle-local `.gitignore`
prevents it from being committed to GitHub.
