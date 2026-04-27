# SCAPE-ZK Caliper Repeated Experiment Bundle

Bundle created: 2026-04-27

This folder categorizes the files used to run, audit, and report the SCAPE-ZK
Hyperledger Fabric repeated Caliper experiment. The primary experiment is the
ten-trial no-txlog run of `benchmark-operations.yaml` on the 4-peer Fabric
network. The txlog files are auxiliary audit data used only for percentile
latency columns, not for the main TPS/average-latency claims.

## 01_run_commands_and_network

Network setup and Fabric test-network configuration copied from:

- `network/fabric-samples/test-network/bring-up-4peer.sh`
- `network/fabric-samples/test-network/benchmark.sh`
- `network/fabric-samples/test-network/network.sh`
- `network/fabric-samples/test-network/setOrgEnv.sh`
- `network/fabric-samples/test-network/compose/docker-compose-peer1.yaml`
- `network/fabric-samples/test-network/configtx/configtx.yaml`
- `network/fabric-samples/test-network/organizations/cryptogen/crypto-config-orderer.yaml`
- `network/fabric-samples/test-network/organizations/cryptogen/crypto-config-org1.yaml`
- `network/fabric-samples/test-network/organizations/cryptogen/crypto-config-org2.yaml`

## 02_chaincode

SCAPE-ZK Go chaincode and Go module files copied from:

- `chaincode-go/scape_zk.go`
- `chaincode-go/go.mod`
- `chaincode-go/go.sum`
- `chaincode-go/perf_test.go`

Vendored dependencies are not duplicated here; the original `chaincode-go/vendor`
tree remains in the repository.

## 03_caliper_workload

Caliper benchmark definitions and workload modules copied from:

- `network/fabric-samples/test-network/caliper-scapezk/benchmark-operations.yaml`
- `network/fabric-samples/test-network/caliper-scapezk/benchmark-operations-txlog.yaml`
- `network/fabric-samples/test-network/caliper-scapezk/benchmark.yaml`
- `network/fabric-samples/test-network/caliper-scapezk/network.yaml`
- `network/fabric-samples/test-network/caliper-scapezk/workloads/operation.js`
- `network/fabric-samples/test-network/caliper-scapezk/workloads/register.js`

The main repeated experiment used `benchmark-operations.yaml`,
`network.yaml`, and `workloads/operation.js`.

## 04_raw_caliper_results

Primary raw no-txlog results copied from:

- `network/fabric-samples/test-network/results/scapezk-caliper-repeated-2026-04-22/caliper-operations-repeated-raw.csv`
- `network/fabric-samples/test-network/results/scapezk-caliper-repeated-2026-04-22/logs/caliper-operations-trial-1.log` through `caliper-operations-trial-10.log`
- `network/fabric-samples/test-network/results/scapezk-caliper-repeated-2026-04-22/reports/caliper-operations-trial-1.html` through `caliper-operations-trial-10.html`
- `network/fabric-samples/test-network/results/scapezk-caliper-repeated-2026-04-22/reports/caliper-operations-warmup.html`

The warm-up HTML report is included for traceability but is excluded from the
reported statistics.

## 05_processed_results

Processed no-txlog summaries and Sheet 03 import CSVs copied from:

- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/caliper-operations-repeated-summary.csv`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/blockchain_tps_sheet03_import.csv`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/blockchain_tps_sheet03_combined_audit_import.csv`

The main manuscript TPS and average-latency values come from these no-txlog
Caliper results.

## 06_figures

Generated figures copied from:

- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/fig_fabric_tps_vs_load.png`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/fig_fabric_tps_vs_load.pdf`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/repeated-throughput-1000tx.svg`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/repeated-latency-1000tx.svg`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/repeated-throughput-by-load.svg`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/figures/repeated-success-summary.svg`

## 07_workbooks

Workbook artifacts copied from:

- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_populated.xlsx`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_combined_audit.xlsx`
- `SCAPE-ZK_Master_Results_v13.xlsx`

## 08_paper_draft_and_audits

Draft and audit notes copied from:

- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/README.md`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/draft/section_7c_7d_draft.md`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/WORKBOOK_AUDIT_FIX.md`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/BLOCKCHAIN_SECTION_VERIFICATION.md`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/MEMBER_C_FEEDBACK_RESPONSE.md`

## 09_reproduction_scripts

Result-processing scripts copied from:

- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/scripts/generate_repeated_figures.py`
- `paper/results/blockchain/scapezk-caliper-repeated-2026-04-22/scripts/generate_combined_sheet03_audit.py`

## 10_txlog_auxiliary

Auxiliary txlog rerun files copied from:

- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/README.md`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/parse_txlog_percentiles.py`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/caliper-operations-txlog-percentiles.csv`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/caliper-operations-txlog-percentiles-summary.csv`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/caliper-operations-txlog-smoke-percentiles.csv`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/logs/caliper-operations-txlog-trial-1.log` through `caliper-operations-txlog-trial-10.log`
- `paper/results/blockchain/scapezk-caliper-txlog-rerun-2026-04-27/reports/caliper-operations-txlog-trial-1.html` through `caliper-operations-txlog-trial-10.html`

These files are not used to replace the main no-txlog TPS values because
transaction logging changes benchmark overhead.

## 11_generated_fabric_identities_and_deploy_script

Generated Fabric identity material and deployment script copied from:

- `network/fabric-samples/test-network/organizations/`
- `network/fabric-samples/test-network/scripts/deployCC.sh`

This category includes generated MSP/TLS private keys referenced by the Caliper
network configuration. It is intentionally ignored by the bundle-local
`.gitignore` and should not be pushed to GitHub unless regenerated or sanitized.

## Main Run Command

The repeated no-txlog experiment used this command shape from the test-network
directory:

```bash
NODE_PATH=/home/slotty666/researchpaper/network/fabric-samples/test-network/node_modules \
npx caliper launch manager \
  --caliper-workspace ./caliper-scapezk \
  --caliper-benchconfig benchmark-operations.yaml \
  --caliper-networkconfig network.yaml \
  --caliper-flow-only-test
```

## Data Boundary

- Main TPS and average-latency claims: use `04_raw_caliper_results` and
  `05_processed_results`.
- Percentile latency audit columns: use `10_txlog_auxiliary`.
- Baseline systems such as XAuth, SSL-XIoMT, and IIoT SSI were not deployed in
  the same Fabric/Caliper environment in this bundle, so this bundle must not
  be used to claim direct baseline TPS comparisons.
