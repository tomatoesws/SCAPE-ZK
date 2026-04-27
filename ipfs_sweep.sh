#!/usr/bin/env bash

set -euo pipefail

API="http://127.0.0.1:5001/api/v0"
RUNS="${RUNS:-10}"
PAYLOADS=(1024 10240 102400 1048576 10485760)
CSV="ipfs_sweep.csv"
LOG="ipfs_sweep.log"

: > "$LOG"
echo "op,payload_bytes,mean_ms,std_ms,n_kept,cids" > "$CSV"

if ! curl -s -f -X POST "$API/id" > /dev/null; then
    echo "ERROR: Kubo API at $API not reachable. Is scape-ipfs up?" >&2
    exit 1
fi

stat_mean_std() {

    python3 - <<'PY'
import sys, statistics
vals = [float(x) for x in sys.stdin.read().split() if x]
kept = vals[1:]
if len(kept) < 2:
    print(f"{kept[0] if kept else 0:.2f} 0.00 {len(kept)}")
else:
    print(f"{statistics.mean(kept):.2f} {statistics.pstdev(kept):.2f} {len(kept)}")
PY
}

for sz in "${PAYLOADS[@]}"; do
    TMP=$(mktemp)
    head -c "$sz" </dev/urandom > "$TMP"

    echo "[payload=$sz B] $RUNS puts..." | tee -a "$LOG"
    put_samples=""
    last_cid=""
    for i in $(seq 1 "$RUNS"); do
        t0=$(date +%s%N)
        CID=$(curl -s -X POST -F file=@"$TMP" "$API/add?quieter=true" \
              | awk -F'"' '/Hash/{print $4; exit}')
        t1=$(date +%s%N)
        ms=$(( (t1 - t0) / 1000000 ))
        echo "  put run=$i ms=$ms cid=$CID" | tee -a "$LOG"
        put_samples+="$ms "
        last_cid="$CID"
    done
    read pmean pstd pn < <(echo "$put_samples" | stat_mean_std)
    echo "put,$sz,$pmean,$pstd,$pn,$last_cid" >> "$CSV"

    echo "[payload=$sz B] $RUNS gets via CID=$last_cid ..." | tee -a "$LOG"
    get_samples=""
    for i in $(seq 1 "$RUNS"); do
        t0=$(date +%s%N)
        curl -s -X POST "$API/cat?arg=$last_cid" > "$TMP.out"
        t1=$(date +%s%N)
        ms=$(( (t1 - t0) / 1000000 ))
        echo "  get run=$i ms=$ms" | tee -a "$LOG"
        get_samples+="$ms "
    done
    read gmean gstd gn < <(echo "$get_samples" | stat_mean_std)
    echo "get,$sz,$gmean,$gstd,$gn,$last_cid" >> "$CSV"

    rm -f "$TMP" "$TMP.out"
done

echo
echo "Done. CSV -> $CSV   Raw log -> $LOG"
echo "Paste target: sheet 06_IPFS, columns C (mean) and D (std) in rows 4-13."
