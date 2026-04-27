from __future__ import annotations

import csv

import os

import statistics

from typing import Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))

def _read(name: str) -> List[Dict[str, str]]:

    p = os.path.join(BASE, name)

    if not os.path.exists(p):

        return []

    with open(p, newline="") as f:

        return list(csv.DictReader(f))

def load_e2e() -> Dict[str, float]:


    rows = _read("e2e_harness.csv")

    by_row: Dict[str, List[float]] = {}

    for r in rows:

        try:

            ms = float(r["phase_ms"])

        except (TypeError, ValueError):

            continue

        key = r.get("component") or r.get("sheet11_row") or "?"

        if not key.strip():

            key = f"row_{r.get('sheet11_row', '?')}"

        by_row.setdefault(key, []).append(ms)

    out: Dict[str, float] = {}

    for k, vs in by_row.items():

        out[k] = statistics.mean(vs) if vs else 0.0

    return out

def scape_zk_total_ms() -> Optional[float]:


    rows = _read("e2e_harness.csv")

    totals = [float(r["phase_ms"]) for r in rows

              if (r.get("component") or "").strip().upper() == "TOTAL"]

    return statistics.mean(totals) if totals else None

def scape_zk_verify_ms() -> Optional[float]:


    rows = _read("e2e_harness.csv")

    candidates: List[float] = []

    for r in rows:

        if r.get("sheet11_row") == "7":

            try:

                candidates.append(float(r["phase_ms"]))

            except (TypeError, ValueError):

                pass

    if candidates:

        return statistics.mean(candidates)

    mins: List[float] = []

    for r in rows:

        comp = (r.get("component") or "").strip().upper()

        if comp == "TOTAL":

            continue

        try:

            mins.append(float(r["phase_ms"]))

        except (TypeError, ValueError):

            pass

    return min(mins) if mins else None

def load_ipfs() -> Dict[int, Dict[str, float]]:


    rows = _read("ipfs_sweep.csv")

    out: Dict[int, Dict[str, float]] = {}

    for r in rows:

        try:

            n = int(r["payload_bytes"])

            ms = float(r["mean_ms"])

        except (TypeError, ValueError, KeyError):

            continue

        d = out.setdefault(n, {})

        d[f"{r['op']}_mean_ms"] = ms

    return out

def load_tshark() -> Dict[str, int]:


    rows = _read("tshark_totals.csv")

    out: Dict[str, int] = {}

    for r in rows:

        try:

            out[r["phase"]] = int(r["bytes_on_wire_total"])

        except (TypeError, ValueError, KeyError):

            continue

    return out

def scape_zk_auth_comm_bytes() -> Optional[int]:


    t = load_tshark()

    pieces = [

        t.get("Session_User-Verifier", 0),

        t.get("Session_Verifier-User", 0),

        t.get("Request_User-Verifier", 0),

        t.get("Request_Verifier-User", 0),

    ]

    s = sum(pieces)

    return s if s > 0 else None

def scape_zk_storage_bytes_for_records(n: int) -> Optional[int]:


    t = load_tshark()

    ipfs_put = t.get("IPFS_put")

    aggr = t.get("Aggregation_Verifier-Chain")

    if not ipfs_put or not aggr:

        return None

    per_record = (ipfs_put + aggr) / 128.0

    return int(per_record * n)

if __name__ == "__main__":

    print("=" * 52)

    print("SCAPE-ZK loader — summary from current CSVs")

    print("=" * 52)

    e2e = load_e2e()

    print("e2e means:")

    for k, v in sorted(e2e.items()):

        print(f"  {k:>10}  {v:6.3f} ms")

    print(f"total_ms:     {scape_zk_total_ms()!r}")

    print(f"verify_ms:    {scape_zk_verify_ms()!r}")

    print(f"auth_comm_B:  {scape_zk_auth_comm_bytes()!r}")

    print(f"storage@128:  {scape_zk_storage_bytes_for_records(128)!r}")

    print("IPFS sweep:")

    for n, d in sorted(load_ipfs().items()):

        print(f"  {n:>10} B   {d}")
