#!/usr/bin/env bash

set -euo pipefail

IF="${IF:-lo}"
BASE_PORT="${BASE_PORT:-49200}"
OUT="tshark_totals.csv"
PCAP_DIR="pcaps"
mkdir -p "$PCAP_DIR"

PHASES=(
    "4:Registration_User-Issuer"
    "5:Registration_Issuer-User"
    "6:Session_User-Verifier"
    "7:Session_Verifier-User"
    "8:Request_User-Verifier"
    "9:Request_Verifier-User"
    "10:Aggregation_Verifier-Chain"
    "11:Revocation_Issuer-Chain"
    "12:PRE_delegate"
    "13:PRE_request"
    "14:IPFS_put"
    "15:IPFS_get"
)

echo "sheet_row,phase,bytes_on_wire_total" > "$OUT"

for p in "${PHASES[@]}"; do
    row="${p%%:*}"
    name="${p##*:}"
    port=$(( BASE_PORT + row - 4 ))
    pcap="$PCAP_DIR/row${row}_${name}.pcap"
    echo "[row $row] capturing $name on $IF:$port -> $pcap"

    tshark -i "$IF" -f "tcp port $port" -a duration:15 -w "$pcap" > /dev/null 2>&1 || true

    total=$(tshark -r "$pcap" -z io,stat,0 2>/dev/null \
            | awk '/Bytes/{getline; getline; print $NF; exit}' \
            | tr -d '[:space:]')
    total="${total:-0}"
    echo "    total bytes = $total"
    echo "$row,$name,$total" >> "$OUT"
done

echo
echo "Done. CSV -> $OUT  PCAPs -> $PCAP_DIR/"
echo "Paste target: sheet 05_Communication, column E (With headers) rows 4..15."
