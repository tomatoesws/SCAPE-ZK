#!/usr/bin/env bash

set -euo pipefail

API="http://127.0.0.1:5001/api/v0"

echo "[1/4] container status"
docker ps --filter "name=scape-ipfs" --format "table {{.Names}}\t{{.Status}}"

echo "[2/4] node ID"
curl -s -X POST "$API/id" | head -c 300; echo

echo "[3/4] put a 1 KiB random payload"
TMP=$(mktemp)
head -c 1024 </dev/urandom > "$TMP"
START_PUT=$(date +%s%N)
CID=$(curl -s -X POST -F file=@"$TMP" "$API/add?quieter=true" | awk -F'"' '/Hash/{print $4}')
END_PUT=$(date +%s%N)
echo "    CID=$CID"
echo "    put latency (ms): $(( (END_PUT - START_PUT) / 1000000 ))"

echo "[4/4] get it back and verify hash matches"
START_GET=$(date +%s%N)
curl -s -X POST "$API/cat?arg=$CID" > "$TMP.out"
END_GET=$(date +%s%N)
echo "    get latency (ms): $(( (END_GET - START_GET) / 1000000 ))"
cmp "$TMP" "$TMP.out" && echo "    round-trip OK"

rm -f "$TMP" "$TMP.out"
echo "Done."
