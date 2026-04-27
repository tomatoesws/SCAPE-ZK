from __future__ import annotations

import csv

import html

import zipfile

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TXLOG_ROOT = ROOT.parent / "scapezk-caliper-txlog-rerun-2026-04-27"

NO_TXLOG_SUMMARY = ROOT / "blockchain_tps_sheet03_import.csv"

TXLOG_SUMMARY = TXLOG_ROOT / "caliper-operations-txlog-percentiles-summary.csv"

CSV_OUT = ROOT / "blockchain_tps_sheet03_combined_audit_import.csv"

XLSX_OUT = ROOT / "SCAPE-ZK_Master_Results_v12_03_Blockchain_TPS_combined_audit.xlsx"

OP_ORDER = [

    ("Register", "register", "yes"),

    ("VerifyProof", "verifyproof", "yes"),

    ("Revoke", "revoke", "yes"),

    ("UpdateCred", "updatecred", "yes"),

    ("RecordExists", "recordexists", "no"),

]

LOADS = [100, 500, 1000]

FIELDS = [

    "operation",

    "load_tx",

    "trials",

    "success_total",

    "fail_total",

    "throughput_tps_mean_no_txlog",

    "throughput_tps_sd_no_txlog",

    "avg_latency_ms_mean_no_txlog",

    "avg_latency_ms_sd_no_txlog",

    "p50_latency_ms_mean_txlog",

    "p50_latency_ms_sd_txlog",

    "p95_latency_ms_mean_txlog",

    "p95_latency_ms_sd_txlog",

    "p99_latency_ms_mean_txlog",

    "p99_latency_ms_sd_txlog",

    "avg_latency_ms_mean_txlog",

    "avg_latency_ms_sd_txlog",

    "source_round",

    "tps_avg_latency_source",

    "percentile_source",

    "include_in_locked_write_template",

    "instrumentation_note",

]

def read_csv_by_key(path: Path, key_fn):

    with path.open(newline="") as fh:

        return {key_fn(row): row for row in csv.DictReader(fh)}

def fmt(value: str, digits: int = 2) -> str:

    if value == "":

        return ""

    return f"{float(value):.{digits}f}"

def build_rows() -> list[dict[str, str]]:

    no_txlog = read_csv_by_key(

        NO_TXLOG_SUMMARY,

        lambda row: (row["operation"], int(row["load_tx"])),

    )

    txlog = read_csv_by_key(TXLOG_SUMMARY, lambda row: row["name"])

    rows = []

    for operation, label_prefix, include in OP_ORDER:

        for load in LOADS:

            base = no_txlog[(operation, load)]

            txlog_row = txlog[f"{label_prefix}-{load}tx"]

            rows.append(

                {

                    "operation": operation,

                    "load_tx": str(load),

                    "trials": base["trials"],

                    "success_total": base["success_total"],

                    "fail_total": base["fail_total"],

                    "throughput_tps_mean_no_txlog": base["throughput_tps_mean"],

                    "throughput_tps_sd_no_txlog": base["throughput_tps_sd"],

                    "avg_latency_ms_mean_no_txlog": base["avg_latency_ms_mean"],

                    "avg_latency_ms_sd_no_txlog": base["avg_latency_ms_sd"],

                    "p50_latency_ms_mean_txlog": fmt(txlog_row["p50_latency_ms_mean"]),

                    "p50_latency_ms_sd_txlog": fmt(txlog_row["p50_latency_ms_sd"]),

                    "p95_latency_ms_mean_txlog": fmt(txlog_row["p95_latency_ms_mean"]),

                    "p95_latency_ms_sd_txlog": fmt(txlog_row["p95_latency_ms_sd"]),

                    "p99_latency_ms_mean_txlog": fmt(txlog_row["p99_latency_ms_mean"]),

                    "p99_latency_ms_sd_txlog": fmt(txlog_row["p99_latency_ms_sd"]),

                    "avg_latency_ms_mean_txlog": fmt(txlog_row["avg_latency_ms_txlog_mean"]),

                    "avg_latency_ms_sd_txlog": fmt(txlog_row["avg_latency_ms_txlog_sd"]),

                    "source_round": base["source_round"],

                    "tps_avg_latency_source": "caliper-operations-repeated-summary.csv / blockchain_tps_sheet03_import.csv",

                    "percentile_source": "../scapezk-caliper-txlog-rerun-2026-04-27/caliper-operations-txlog-percentiles-summary.csv",

                    "include_in_locked_write_template": include,

                    "instrumentation_note": "TPS and average latency use no-txlog Caliper run; p50/p95/p99 use txlog-instrumented rerun.",

                }

            )

    return rows

def write_csv(rows: list[dict[str, str]]) -> None:

    with CSV_OUT.open("w", newline="") as fh:

        writer = csv.DictWriter(fh, fieldnames=FIELDS)

        writer.writeheader()

        writer.writerows(rows)

def cell_ref(row: int, col: int) -> str:

    letters = ""

    while col:

        col, rem = divmod(col - 1, 26)

        letters = chr(65 + rem) + letters

    return f"{letters}{row}"

def cell_xml(row: int, col: int, value: str) -> str:

    ref = cell_ref(row, col)

    try:

        numeric = value != "" and str(float(value)) not in {"nan", "inf", "-inf"}

    except ValueError:

        numeric = False

    if numeric and not value.startswith("0"):

        return f'<c r="{ref}"><v>{html.escape(value)}</v></c>'

    return f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(value)}</t></is></c>'

def row_xml(row_index: int, values: list[str]) -> str:

    cells = "".join(cell_xml(row_index, col, value) for col, value in enumerate(values, start=1))

    return f'<row r="{row_index}">{cells}</row>'

def write_xlsx(rows: list[dict[str, str]]) -> None:

    intro_rows = [

        ["SCAPE-ZK Master Results v12 - Sheet 03 combined audit patch"],

        ["Rows 7-21 keep no-txlog TPS/average latency separate from txlog percentile latency."],

        ["Do not silently replace no-txlog TPS with txlog TPS; txlog run logs every transaction."],

        ["RecordExists is read-only and marked no for the locked write-operation template."],

        [],

        FIELDS,

    ]

    sheet_rows = []

    for index, values in enumerate(intro_rows, start=1):

        sheet_rows.append(row_xml(index, values))

    for offset, row in enumerate(rows, start=7):

        sheet_rows.append(row_xml(offset, [row[field] for field in FIELDS]))

    sheet_xml = (

        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'

        '<sheetData>'

        + "".join(sheet_rows)

        + "</sheetData></worksheet>"

    )

    workbook_xml = (

        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '

        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'

        '<sheets><sheet name="03_Blockchain_TPS" sheetId="1" r:id="rId1"/></sheets></workbook>'

    )

    rels_xml = (

        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'

        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'

        "</Relationships>"

    )

    workbook_rels_xml = (

        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'

        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'

        "</Relationships>"

    )

    content_types_xml = (

        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'

        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'

        '<Default Extension="xml" ContentType="application/xml"/>'

        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'

        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'

        "</Types>"

    )

    with zipfile.ZipFile(XLSX_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:

        zf.writestr("[Content_Types].xml", content_types_xml)

        zf.writestr("_rels/.rels", rels_xml)

        zf.writestr("xl/workbook.xml", workbook_xml)

        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)

        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)

def main() -> int:

    rows = build_rows()

    write_csv(rows)

    write_xlsx(rows)

    print(f"wrote {CSV_OUT}")

    print(f"wrote {XLSX_OUT}")

    return 0

if __name__ == "__main__":

    raise SystemExit(main())
