# Workbook Audit Fix for 03_Blockchain_TPS

This bundle fixes the broken audit chain for Section 7.C by providing populated
workbook-ready data derived from the repeated Caliper source CSV.

## Files

- `caliper-operations-repeated-summary.csv`: source aggregate benchmark data.
- `blockchain_tps_sheet03_import.csv`: CSV extract for the master workbook.
- `blockchain_tps_sheet03_combined_audit_import.csv`: updated Sheet 03 import
  CSV that preserves no-txlog TPS/average-latency columns and adds
  txlog-instrumented p50/p95/p99 columns.
- `SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_populated.xlsx`: populated
  single-sheet workbook patch with sheet name `03_Blockchain_TPS`.
- `SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_combined_audit.xlsx`:
  single-sheet workbook patch using the combined audit schema.
- `SCAPE-ZK_Master_Results_v11_03_Blockchain_TPS_populated.xlsx`: earlier
  copy retained for traceability.

## Audit Rules Applied

- Latency is reported in milliseconds, matching the locked unit convention.
- Warm-up run is excluded.
- Statistics are mean and sample standard deviation across 10 logged Caliper
  trials.
- Throughput and average latency in columns F-I come from the original no-txlog
  repeated Caliper run.
- Percentile latency columns J-O come from the txlog-instrumented rerun in
  `../scapezk-caliper-txlog-rerun-2026-04-27/`.
- The txlog rerun is not used to replace the no-txlog TPS values because logging
  every transaction lowers measured throughput.
- `Register`, `VerifyProof`, `Revoke`, and `UpdateCred` are marked as included
  in the locked write-operation template.
- `RecordExists` is included for traceability but marked `no` for the locked
  write-operation template because it is a read-only query and was not present
  in the original sheet row template.

## Required Workbook Action

Copy/import the `03_Blockchain_TPS` sheet from
`SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_combined_audit.xlsx` into the
real master workbook as v12, or paste the rows from
`blockchain_tps_sheet03_combined_audit_import.csv` into the existing
`03_Blockchain_TPS` sheet.

The real master workbook was not present in this workspace, so it could not be
patched in place.
