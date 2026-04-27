from __future__ import annotations

import argparse, csv, socket, struct, sys, time

from contextlib import contextmanager

PHASES = [

    (4,  'Registration upstream',   'CP-ABE + Issuer',       176,   0),

    (5,  'Registration downstream', 'CP-ABE + Issuer',         0, 1776),

    (6,  'Session prove upstream',  'Groth16 Session',       952,   0),

    (7,  'Session token downstream','Groth16 Session',         0,   96),

    (8,  'Request prove upstream',  'Groth16 Request',       952,   0),

    (9,  'Request response',        'Groth16 Request',         0,  256),

    (10, 'Aggregation',             'BLS aggregate',         344,   0),

    (11, 'Revocation',              'Fabric',                328,   0),

    (12, 'PRE delegate',            'PRE',                   144,   0),

    (13, 'PRE request',             'PRE',                   256,   0),

    (14, 'IPFS put',                'Kubo',                 1024,   0),

    (15, 'IPFS get',                'Kubo',                    0, 1024),

]

ELEVEN_ROW = {

    4: 4, 5: 4,

    6: 5, 7: 5,

    10: 6, 11: 6,

    8: 7, 9: 7,

    12: 9, 13: 9,

    14: 10, 15: 10,

}

def _send_n(sock: socket.socket, n: int) -> None:

    buf = b'\x00' * 4096

    while n > 0:

        k = sock.send(buf[:min(n, len(buf))])

        n -= k

def _recv_n(sock: socket.socket, n: int) -> None:

    while n > 0:

        chunk = sock.recv(min(n, 65536))

        if not chunk:

            return

        n -= len(chunk)

@contextmanager

def server(host: str, port: int, up: int, down: int):


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((host, port)); s.listen(1)

    import threading

    def run():

        try:

            c, _ = s.accept()

            if up:   _recv_n(c, up)

            if down: _send_n(c, down)

            c.close()

        except Exception:

            pass

    t = threading.Thread(target=run, daemon=True); t.start()

    try: yield

    finally: s.close(); t.join(timeout=1)

def run_phase(host: str, port: int, up: int, down: int) -> float:


    t0 = time.perf_counter_ns()

    with server(host, port, up, down):

        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        c.connect((host, port))

        if up:   _send_n(c, up)

        if down: _recv_n(c, down)

        c.close()

    t1 = time.perf_counter_ns()

    return (t1 - t0) / 1_000_000.0

def main():

    ap = argparse.ArgumentParser()

    ap.add_argument('--host', default='127.0.0.1')

    ap.add_argument('--base-port', type=int, default=49200)

    ap.add_argument('--runs', type=int, default=5)

    ap.add_argument('--out',  default='e2e_harness.csv')

    args = ap.parse_args()

    per_run = {r: [] for r in sorted(set(ELEVEN_ROW.values()))}

    per_run[8] = []

    per_run[11] = []

    with open(args.out, 'w', newline='') as f:

        w = csv.writer(f)

        w.writerow(['run','sheet11_row','component','phase_ms'])

        for run in range(1, args.runs + 1):

            totals_by_row: dict[int,float] = {}

            for (sheet5_row, step, comp, up, down) in PHASES:

                port = args.base_port + sheet5_row - 4

                ms   = run_phase(args.host, port, up, down)

                tgt  = ELEVEN_ROW.get(sheet5_row)

                if tgt is not None:

                    totals_by_row[tgt] = totals_by_row.get(tgt, 0.0) + ms

                sys.stderr.write(f'  run={run} row5={sheet5_row} {step:28s} {ms:8.3f} ms\n')

            for r, ms in totals_by_row.items():

                w.writerow([run, r, '', f'{ms:.3f}'])

                per_run[r].append(ms)

            total = sum(totals_by_row.values())

            w.writerow([run, 11, 'TOTAL', f'{total:.3f}'])

            per_run[11].append(total)

    sys.stderr.write('\nSummary (paste into 11_E2E_Integration C..G for rows 4..11):\n')

    for r in sorted(per_run):

        vs = per_run[r]

        if not vs: continue

        sys.stderr.write(f'  row {r}: {", ".join(f"{v:.3f}" for v in vs)}\n')

if __name__ == '__main__':

    main()
