from __future__ import annotations

import math

from .common import OPS_TYPEF_I7 as _OPS, SIZES_TYPEF as _S

def bctrt_verify_ms(n_certs: int) -> float:


    return 13.52 * n_certs

def bctrt_inquiry_ms(n_certs: int) -> float:


    return 50.0 * math.exp(n_certs / 32.0)

def certchain_verify_ms(n_certs: int) -> float:


    return 18.0 * n_certs

def certledger_verify_ms(n_certs: int) -> float:


    return 23.0 * n_certs

_MS_PER_PROOF = {

    "scheme31": 522.30,

    "scheme29": 109.70,

    "scheme27": 260.00,

    "scheme28": 310.00,

}

def sslxiomt_peer_time_ms(n_proofs: int, scheme: str) -> float:


    if scheme not in _MS_PER_PROOF:

        raise ValueError(scheme)

    return _MS_PER_PROOF[scheme] * n_proofs

def sslxiomt_peer_encrypt_ms(data_kb: float, n_attrs: int, scheme: str) -> float:



    base = 5.5 + 0.42 * n_attrs + max(0.5, data_kb * 0.12)

    mult = {"scheme29": 1.85, "scheme31": 1.35, "scheme27": 1.55, "scheme28": 1.45}

    return base * mult[scheme]

def ma_showcred_ms(n_k: int, n_I: int) -> float:



    return 3 * _OPS.T_sm + _OPS.T_mul + 6 * _OPS.T_h

def shi_showcred_ms(n_k: int, n_I: int) -> float:


    n_total = 50

    return (n_total - n_k) * _OPS.T_sm + 4 * _OPS.T_pair

def hebant_showcred_ms(n_k: int, n_I: int) -> float:


    return n_k * _OPS.T_sm + 2 * _OPS.T_pair + _OPS.T_mul

def fuchsbauer_showcred_ms(n_k: int, n_I: int) -> float:


    return n_I * (2 * _OPS.T_pair + _OPS.T_sm) + n_k * _OPS.T_sm

def su_showcred_ms(n_k: int, n_I: int) -> float:


    return n_I * (_OPS.T_pair + 2 * _OPS.T_sm) + 5 * _OPS.T_h

def ma_verify_ms(n_k: int, n_I: int) -> float:


    return 2 * _OPS.T_pair + _OPS.T_mul

def shi_verify_ms(n_k: int, n_I: int) -> float:

    return 2 * _OPS.T_pair + n_k * _OPS.T_sm + (n_I * _OPS.T_h)

def hebant_verify_ms(n_k: int, n_I: int) -> float:

    return 2 * _OPS.T_pair + n_k * _OPS.T_sm

def fuchsbauer_verify_ms(n_k: int, n_I: int) -> float:

    return n_I * 2 * _OPS.T_pair + n_k * _OPS.T_sm

def su_verify_ms(n_k: int, n_I: int) -> float:

    return n_I * _OPS.T_pair + n_k * _OPS.T_sm

def ma_comm_bytes(n_k_total: int, n_I: int) -> int:


    return n_k_total * (3 * _S.G1) + (2 * _S.G1 + _S.Zp)

def shi_comm_bytes(n_k_total: int, n_I: int) -> int:


    return n_I * (2 * _S.G1 + _S.G2) + _S.H

def fuchsbauer_comm_bytes(n_k_total: int, n_I: int) -> int:


    attrs_per_issuer = max(1, n_k_total // max(1, n_I))

    return n_I * (2 * _S.G1 + _S.Zp + attrs_per_issuer * _S.G1 + _S.H)

def su_comm_bytes(n_k_total: int, n_I: int) -> int:


    attrs_per_issuer = max(1, n_k_total // max(1, n_I))

    return n_I * (2 * _S.G1 + attrs_per_issuer * _S.G1) + _S.H

def hebant_comm_bytes(n_k_total: int, n_I: int) -> int:


    return 2 * _S.G1 + _S.Zp + _S.H

def scheme30_comm_bytes(n_k_disclosed: int, n_I: int) -> int:


    return 2 * _S.G1 + _S.Zp + n_k_disclosed * _S.G1 + _S.H

XAUTH_PEERS = {

    "XAuth":        lambda n: 5.0 * n,

    "BCTRT":        bctrt_verify_ms,

    "CertChain":    certchain_verify_ms,

    "CertLedger":   certledger_verify_ms,

}

SSLXIOMT_PEERS = {

    "SSL-XIoMT":    lambda n: 6.94 * n,

    "Scheme [31]":  lambda n: _MS_PER_PROOF["scheme31"] * n,

    "Scheme [29]":  lambda n: _MS_PER_PROOF["scheme29"] * n,

    "Scheme [27]":  lambda n: _MS_PER_PROOF["scheme27"] * n,

    "Scheme [28]":  lambda n: _MS_PER_PROOF["scheme28"] * n,

}

SCHEME30_SHOWCRED_PEERS = {

    "Scheme [30]":   lambda k, I: k * _OPS.T_sm + I * _OPS.T_h + _OPS.T_mul,

    "Ma [31]":       ma_showcred_ms,

    "Shi [14]":      shi_showcred_ms,

    "Hébant [32]":   hebant_showcred_ms,

    "Fuchsbauer [13]": fuchsbauer_showcred_ms,

    "Su [27]":       su_showcred_ms,

}

SCHEME30_COMM_PEERS = {

    "Scheme [30]":     scheme30_comm_bytes,

    "Ma [31]":         ma_comm_bytes,

    "Shi [14]":        shi_comm_bytes,

    "Fuchsbauer [13]": fuchsbauer_comm_bytes,

    "Su [27]":         su_comm_bytes,

    "Hébant [32]":     hebant_comm_bytes,

}
