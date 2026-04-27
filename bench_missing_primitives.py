from __future__ import annotations

import hashlib

import os

import statistics

import time

OPS = 1000

def ms_per_op(fn, ops: int = OPS) -> tuple[float, float]:

    samples: list[float] = []

    for _ in range(ops):

        start = time.perf_counter_ns()

        fn()

        end = time.perf_counter_ns()

        samples.append((end - start) / 1_000_000.0)

    return statistics.mean(samples), statistics.stdev(samples)

def bench_sha256_1kb() -> None:

    payload = bytes([i % 251 for i in range(1024)])

    def op() -> None:

        hashlib.sha256(payload).digest()

    mean, std = ms_per_op(op)

    print(f"Thash_1KB_sha256_ms,{mean:.9f},{std:.9f},{OPS}")

def bench_aes_gcm_decrypt_1kb() -> None:

    try:

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    except ImportError as exc:

        raise SystemExit(

            "Missing cryptography. Run this in the same environment you use for "

            "scripts/bench_cpabe.py."

        ) from exc

    key = os.urandom(32)

    nonce = os.urandom(12)

    aad = b"scape-zk-missing-primitive-bench"

    plaintext = bytes([i % 251 for i in range(1024)])

    aes = AESGCM(key)

    ciphertext = aes.encrypt(nonce, plaintext, aad)

    def op() -> None:

        aes.decrypt(nonce, ciphertext, aad)

    mean, std = ms_per_op(op)

    print(f"Tsym_dec_AES_256_GCM_1KB_ms,{mean:.9f},{std:.9f},{OPS}")

def bench_ecdsa_p256_verify_sha256() -> None:

    try:

        from cryptography.exceptions import InvalidSignature

        from cryptography.hazmat.primitives import hashes

        from cryptography.hazmat.primitives.asymmetric import ec

    except ImportError as exc:

        raise SystemExit(

            "Missing cryptography. Run this in the same environment you use for "

            "scripts/bench_cpabe.py."

        ) from exc

    key = ec.generate_private_key(ec.SECP256R1())

    public_key = key.public_key()

    message = b"scape-zk-ecdsa-verify-message"

    signature = key.sign(message, ec.ECDSA(hashes.SHA256()))

    def op() -> None:

        try:

            public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))

        except InvalidSignature as exc:

            raise RuntimeError("ECDSA verification failed") from exc

    mean, std = ms_per_op(op)

    print(f"Tecc_verify_ECDSA_P256_SHA256_ms,{mean:.9f},{std:.9f},{OPS}")

def bench_charm_exponentiations() -> None:

    try:

        from charm.toolbox.pairinggroup import G1, G2, GT, ZR, PairingGroup, pair

    except ImportError as exc:

        raise SystemExit(

            "Missing charm-crypto. Run this in the same environment you use for "

            "scripts/bench_cpabe.py and scripts/bench_pre.py."

        ) from exc

    group = PairingGroup("SS512")

    g1 = group.random(G1)

    h1 = group.random(G1)

    g2 = group.random(G2)

    h2 = group.random(G2)

    gt = pair(g1, h1)

    z = group.random(ZR)

    def g1_exp() -> None:

        g1 ** z

    def gt_exp() -> None:

        gt ** z

    def g1_mul() -> None:

        g1 * h1

    def g2_mul() -> None:

        g2 * h2

    mean, std = ms_per_op(g1_exp)

    print(f"Texp_G1_charm_SS512_ms,{mean:.9f},{std:.9f},{OPS}")

    mean, std = ms_per_op(gt_exp)

    print(f"Texp_GT_charm_SS512_ms,{mean:.9f},{std:.9f},{OPS}")

    mean, std = ms_per_op(g1_mul)

    print(f"TE2_G1_mul_charm_SS512_ms,{mean:.9f},{std:.9f},{OPS}")

    mean, std = ms_per_op(g2_mul)

    print(f"TE2_G2_mul_charm_SS512_ms,{mean:.9f},{std:.9f},{OPS}")

def main() -> None:

    print("primitive,mean_ms,std_ms,ops")

    bench_sha256_1kb()

    bench_aes_gcm_decrypt_1kb()

    bench_ecdsa_p256_verify_sha256()

    bench_charm_exponentiations()

if __name__ == "__main__":

    main()
