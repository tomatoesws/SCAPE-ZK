from __future__ import annotations

import os

import sys

import time

import statistics

from typing import Callable

BATCHES = [1, 10, 50, 100, 200]

RUNS    = 10

def _blspy_backend():


    from blspy import (AugSchemeMPL, PrivateKey, G1Element, G2Element)

    import secrets

    scheme = AugSchemeMPL

    def keygen():

        seed = secrets.token_bytes(32)

        sk = scheme.key_gen(seed)

        pk = sk.get_g1()

        return sk, pk

    def sign(sk, msg):     return scheme.sign(sk, msg)

    def verify(pk, msg, sig): return scheme.verify(pk, msg, sig)

    def aggregate(sigs):   return scheme.aggregate(sigs)

    def aggregate_verify(pks, msgs, agg_sig):

        return scheme.aggregate_verify(pks, msgs, agg_sig)

    return dict(name='blspy/blst',

                keygen=keygen, sign=sign, verify=verify,

                aggregate=aggregate, aggregate_verify=aggregate_verify)

def _pyecc_backend():


    from py_ecc.bls import G2ProofOfPossession as scheme

    import secrets

    def keygen():

        sk_int = int.from_bytes(secrets.token_bytes(32), 'big') or 1

        sk_bytes = sk_int.to_bytes(32, 'big')

        sk = scheme.KeyGen(sk_bytes)

        pk = scheme.SkToPk(sk)

        return sk, pk

    def sign(sk, msg):     return scheme.Sign(sk, msg)

    def verify(pk, msg, sig): return scheme.Verify(pk, msg, sig)

    def aggregate(sigs):   return scheme.Aggregate(sigs)

    def aggregate_verify(pks, msgs, agg_sig):

        return scheme.AggregateVerify(pks, msgs, agg_sig)

    return dict(name='py_ecc/pure-python (REFERENCE ONLY)',

                keygen=keygen, sign=sign, verify=verify,

                aggregate=aggregate, aggregate_verify=aggregate_verify)

def pick_backend():

    prefer = os.environ.get('BLS_BACKEND', 'blspy').lower()

    order = [prefer] + [x for x in ('blspy','pyecc') if x != prefer]

    errs = []

    for name in order:

        try:

            return (_blspy_backend() if name == 'blspy' else _pyecc_backend())

        except Exception as e:

            errs.append(f'{name}: {e!r}')

    sys.stderr.write('No BLS backend available:\n  ' + '\n  '.join(errs) + '\n')

    sys.stderr.write('Install one of:  pip install blspy   OR   pip install py_ecc\n')

    sys.exit(2)

def _time(fn: Callable[[], None]) -> float:

    t0 = time.perf_counter_ns()

    fn()

    t1 = time.perf_counter_ns()

    return (t1 - t0) / 1_000_000.0

def bench_one_batch(backend, batch: int):


    sign_runs, verify_runs = [], []

    for _ in range(RUNS):

        keys  = [backend['keygen']() for _ in range(batch)]

        msgs  = [os.urandom(32) for _ in range(batch)]

        sks   = [sk for (sk, _pk) in keys]

        pks   = [pk for (_sk, pk) in keys]

        def do_sign():

            sigs = [backend['sign'](sk, m) for sk, m in zip(sks, msgs)]

            return backend['aggregate'](sigs)

        t_sign = _time(do_sign)

        sign_runs.append(t_sign)

        sigs = [backend['sign'](sk, m) for sk, m in zip(sks, msgs)]

        agg  = backend['aggregate'](sigs)

        t_ver = _time(lambda: backend['aggregate_verify'](pks, msgs, agg))

        verify_runs.append(t_ver)

    return sign_runs, verify_runs

def main():

    backend = pick_backend()

    sys.stderr.write(f'[bls_bench] backend = {backend["name"]}\n')

    out = []

    for batch in BATCHES:

        sys.stderr.write(f'[bls_bench] batch={batch} ...\n')

        sign_runs, verify_runs = bench_one_batch(backend, batch)

        out.append(('Aggregate sign',  batch, sign_runs))

        out.append(('Aggregate verify', batch, verify_runs))

    print('operation,batch,' +

          ','.join(f'run_{i+1}' for i in range(RUNS)) +

          ',backend')

    for op, batch, runs in out:

        kept = runs[1:]

        mean = statistics.mean(kept)

        std  = statistics.pstdev(kept) if len(kept) > 1 else 0.0

        sys.stderr.write(f'  {op:17s} batch={batch:3d}  '

                         f'mean={mean:9.3f} ms  std={std:7.3f}  (n={len(kept)})\n')

        row = [op, str(batch)] + [f'{x:.3f}' for x in runs] + [backend['name']]

        print(','.join(row))

if __name__ == '__main__':

    main()
