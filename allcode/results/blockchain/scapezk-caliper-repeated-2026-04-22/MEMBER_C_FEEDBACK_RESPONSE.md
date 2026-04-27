# Member C Feedback Response - Sheet 03 / Sheet 04

Date: 2026-04-27

## Sheet 03

Member C is correct that the real master workbook remains unauditable if its
`03_Blockchain_TPS` sheet is still empty. The real master workbook is not
present in this workspace, so it was not patched in place.

What is present here:

- `caliper-operations-repeated-raw.csv`: 10 trials x 15 Caliper rounds.
- `caliper-operations-repeated-summary.csv`: recomputed aggregate means and
  sample standard deviations.
- `blockchain_tps_sheet03_import.csv`: paste/import CSV for `03_Blockchain_TPS`.
- `blockchain_tps_sheet03_combined_audit_import.csv`: updated paste/import CSV
  that preserves no-txlog TPS/average-latency values and adds p50/p95/p99 from
  the txlog rerun.
- `SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_populated.xlsx`: one-sheet
  workbook patch named `03_Blockchain_TPS`.
- `SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_combined_audit.xlsx`: updated
  one-sheet workbook patch named `03_Blockchain_TPS`.

The populated patch uses the schema implied by the audit comments:

- Rows 7-21.
- Five operations: `Register`, `VerifyProof`, `Revoke`, `UpdateCred`,
  `RecordExists`.
- Three rows per operation: 100, 500, and 1000 tx.
- Columns F/G contain throughput mean/SD.
- Columns H/I contain average latency mean/SD in milliseconds.
- Columns J-O contain p50/p95/p99 mean/SD from the txlog-instrumented rerun.
- Columns P/Q contain txlog average latency mean/SD for cross-checking.

The specific forwarded cells exist in the patch:

- `03!F9,G9`: Register 1000 tx throughput mean/SD.
- `03!F12,G12`: VerifyProof 1000 tx throughput mean/SD.
- `03!F15,G15`: Revoke 1000 tx throughput mean/SD.
- `03!F18,G18`: UpdateCred 1000 tx throughput mean/SD.
- `03!F21,G21`: RecordExists 1000 tx throughput mean/SD.

Action needed: import/copy the combined audit patch into the real master
workbook, or paste `blockchain_tps_sheet03_combined_audit_import.csv` into the
real `03_Blockchain_TPS` sheet.

## Caliper Bundle Limitation

The original no-txlog Caliper reports/logs expose success, failure, send rate,
min/max/average latency, and throughput. They do not expose p50/p95/p99 latency.

To close that gap, B reran the 15-round benchmark with Caliper's transaction
logging observer enabled:

- 10 full trials.
- 8,000 transaction-level records per trial.
- 80,000 total full-run `txInfo` records.
- All full trials exited `rc=0`.
- Percentiles are computed from `time_final - time_create`.

Important caveat: the txlog rerun logs every transaction, so its throughput is
lower than the no-txlog benchmark. The combined Sheet 03 patch keeps no-txlog
TPS/average latency as the authoritative TPS columns and uses the txlog rerun
only for p50/p95/p99 audit columns.

## Sheet 04 / F7

Sheet 04 source data is still not present here. There is no auditable source for
endorsement latency, commit latency, CPU-ms/tx, RAM peak, or the §7.F.2 26x
headline if it depends on the 50 ms placeholder.

Recommended standup decision:

- If Sheet 04 was not measured this sprint, drop the 26x §7.F.2 claim and drop
  `fig_contract_cost_bars.png` / F7 from §7.D.
- If Sheet 04 was measured elsewhere, provide the raw data and then render F7
  from that source.
