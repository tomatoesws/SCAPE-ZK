from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
import uuid
from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def aesgcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> Dict[str, str]:
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return {"nonce": b64(nonce), "ciphertext": b64(ciphertext)}


def aesgcm_decrypt(key: bytes, bundle: Dict[str, str], aad: bytes = b"") -> bytes:
    return AESGCM(key).decrypt(b64d(bundle["nonce"]), b64d(bundle["ciphertext"]), aad)


def hkdf_like(*parts: bytes) -> bytes:
    state = b"ssl-xiomt-hkdf"
    for part in parts:
        state = sha256_bytes(state + part)
    return state


def derive_aes_key(*parts: bytes) -> bytes:
    return hkdf_like(*parts)


def sign_payload(private_key: ec.EllipticCurvePrivateKey, payload: Dict[str, Any]) -> str:
    signature = private_key.sign(canonical_json(payload), ec.ECDSA(hashes.SHA256()))
    return b64(signature)


def verify_signature(
    public_key: ec.EllipticCurvePublicKey, payload: Dict[str, Any], signature_b64: str
) -> bool:
    try:
        public_key.verify(b64d(signature_b64), canonical_json(payload), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def pem_public_key(public_key: ec.EllipticCurvePublicKey) -> str:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def pem_x25519_public_key(public_key: x25519.X25519PublicKey) -> str:
    return b64(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
    )


def load_x25519_public_key(encoded: str) -> x25519.X25519PublicKey:
    return x25519.X25519PublicKey.from_public_bytes(b64d(encoded))


def split_bytes(data: bytes) -> Tuple[bytes, bytes]:
    midpoint = len(data) // 2
    return data[:midpoint], data[midpoint:]


def additive_shares(secret: bytes, parts: int = 3) -> List[str]:
    integers = [int.from_bytes(secrets.token_bytes(len(secret)), "big") for _ in range(parts - 1)]
    secret_int = int.from_bytes(secret, "big")
    modulus = 1 << (8 * len(secret))
    last = (secret_int - sum(integers)) % modulus
    integers.append(last)
    width = len(secret)
    return [b64(i.to_bytes(width, "big")) for i in integers]


@dataclass(frozen=True)
class PolicyNode:
    kind: str
    attribute: Optional[str] = None
    threshold: Optional[int] = None
    children: Tuple["PolicyNode", ...] = ()

    @staticmethod
    def leaf(attribute: str) -> "PolicyNode":
        return PolicyNode(kind="LEAF", attribute=attribute)

    @staticmethod
    def op(kind: str, *children: "PolicyNode", threshold: Optional[int] = None) -> "PolicyNode":
        return PolicyNode(kind=kind, children=tuple(children), threshold=threshold)

    def evaluate(self, attributes: Set[str]) -> bool:
        if self.kind == "LEAF":
            return self.attribute in attributes
        if self.kind == "AND":
            return all(child.evaluate(attributes) for child in self.children)
        if self.kind == "OR":
            return any(child.evaluate(attributes) for child in self.children)
        if self.kind == "MOFN":
            threshold = self.threshold or 0
            return sum(1 for child in self.children if child.evaluate(attributes)) >= threshold
        raise ValueError(f"unsupported policy kind: {self.kind}")

    def all_attributes(self) -> Set[str]:
        if self.kind == "LEAF":
            return {self.attribute or ""}
        attrs: Set[str] = set()
        for child in self.children:
            attrs.update(child.all_attributes())
        return attrs

    def ordered(self) -> "PolicyNode":
        if self.kind == "LEAF":
            return self
        weight = {"AND": 0, "MOFN": 1, "OR": 2, "LEAF": 3}
        ordered_children = tuple(child.ordered() for child in self.children)
        return PolicyNode(
            kind=self.kind,
            threshold=self.threshold,
            children=tuple(sorted(ordered_children, key=lambda child: weight[child.kind])),
        )

    def minimal_satisfying_sets(self) -> List[Set[str]]:
        if self.kind == "LEAF":
            return [{self.attribute or ""}]
        child_sets = [child.minimal_satisfying_sets() for child in self.children]
        results: List[Set[str]] = []
        if self.kind == "AND":
            for combo in product(*child_sets):
                merged: Set[str] = set()
                for subset in combo:
                    merged.update(subset)
                results.append(merged)
        elif self.kind == "OR":
            for options in child_sets:
                results.extend(set(option) for option in options)
        elif self.kind == "MOFN":
            threshold = self.threshold or 0
            for child_indexes in combinations(range(len(self.children)), threshold):
                selected = [child_sets[index] for index in child_indexes]
                for combo in product(*selected):
                    merged: Set[str] = set()
                    for subset in combo:
                        merged.update(subset)
                    results.append(merged)
        else:
            raise ValueError(f"unsupported policy kind: {self.kind}")
        return dedupe_minimal_sets(results)


def dedupe_minimal_sets(candidates: Iterable[Set[str]]) -> List[Set[str]]:
    unique = []
    for candidate in sorted((set(item) for item in candidates), key=lambda item: (len(item), sorted(item))):
        if any(existing <= candidate for existing in unique):
            continue
        unique = [existing for existing in unique if not candidate < existing]
        unique.append(candidate)
    return unique


@dataclass
class MerkleTree:
    leaves: List[bytes]
    levels: List[List[bytes]]

    @property
    def root(self) -> str:
        return self.levels[-1][0].hex()

    def proof(self, index: int) -> List[Dict[str, str]]:
        proof_path: List[Dict[str, str]] = []
        idx = index
        for level in self.levels[:-1]:
            sibling_idx = idx ^ 1
            sibling = level[sibling_idx] if sibling_idx < len(level) else level[idx]
            direction = "left" if sibling_idx < idx else "right"
            proof_path.append({"direction": direction, "hash": sibling.hex()})
            idx //= 2
        return proof_path

    @staticmethod
    def build(values: Sequence[bytes]) -> "MerkleTree":
        if not values:
            raise ValueError("merkle tree requires at least one leaf")
        levels = [[sha256_bytes(value) for value in values]]
        while len(levels[-1]) > 1:
            current = levels[-1]
            next_level = []
            for index in range(0, len(current), 2):
                left = current[index]
                right = current[index + 1] if index + 1 < len(current) else current[index]
                next_level.append(sha256_bytes(left + right))
            levels.append(next_level)
        return MerkleTree(leaves=list(values), levels=levels)

    @staticmethod
    def verify(leaf: bytes, proof: Sequence[Dict[str, str]], root: str) -> bool:
        current = sha256_bytes(leaf)
        for item in proof:
            sibling = bytes.fromhex(item["hash"])
            if item["direction"] == "left":
                current = sha256_bytes(sibling + current)
            else:
                current = sha256_bytes(current + sibling)
        return current.hex() == root


@dataclass
class ConsortiumLedger:
    credentials: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    proofs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    merkle_roots: Dict[str, str] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def record_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.events.append({"event_type": event_type, "payload": payload, "ts": time.time()})


@dataclass
class AttributeAuthority:
    master_signing_key: ec.EllipticCurvePrivateKey = field(
        default_factory=lambda: ec.generate_private_key(ec.SECP256R1())
    )
    attribute_keys: Dict[str, x25519.X25519PrivateKey] = field(default_factory=dict)

    def ensure_attribute(self, attribute: str) -> None:
        if attribute not in self.attribute_keys:
            self.attribute_keys[attribute] = x25519.X25519PrivateKey.generate()

    def attribute_public_key(self, attribute: str) -> x25519.X25519PublicKey:
        self.ensure_attribute(attribute)
        return self.attribute_keys[attribute].public_key()

    def issue_attribute_private_key(self, attribute: str) -> x25519.X25519PrivateKey:
        self.ensure_attribute(attribute)
        return self.attribute_keys[attribute]


@dataclass
class SSIWallet:
    did: str
    attributes: Set[str]
    signing_key: ec.EllipticCurvePrivateKey = field(default_factory=lambda: ec.generate_private_key(ec.SECP256R1()))
    transport_key: x25519.X25519PrivateKey = field(default_factory=x25519.X25519PrivateKey.generate)
    credential: Optional[Dict[str, Any]] = None
    vc_signature: Optional[str] = None
    attribute_private_keys: Dict[str, x25519.X25519PrivateKey] = field(default_factory=dict)

    @property
    def public_identity_key(self) -> ec.EllipticCurvePublicKey:
        return self.signing_key.public_key()

    @property
    def public_transport_key(self) -> x25519.X25519PublicKey:
        return self.transport_key.public_key()


@dataclass
class DataOwner:
    owner_id: str
    wallet: SSIWallet


@dataclass
class DataUser:
    user_id: str
    wallet: SSIWallet
    trustiness: str = "verified"


@dataclass
class FogProxy:
    domain_id: str
    private_key: x25519.X25519PrivateKey = field(default_factory=x25519.X25519PrivateKey.generate)

    @property
    def public_key(self) -> x25519.X25519PublicKey:
        return self.private_key.public_key()


@dataclass
class StoredRecord:
    record_id: str
    ctm: Dict[str, str]
    ctrv1: Dict[str, Any]
    proxy_payload: Dict[str, str]
    merkle_leaf: bytes
    merkle_root: str
    merkle_proof: List[Dict[str, str]]
    owner_did: str
    policy_root_kind: str


class SSLXIoMTSystem:
    def __init__(self) -> None:
        self.aa = AttributeAuthority()
        self.ledger = ConsortiumLedger()
        self.domain_proxies = {
            "domain-a": FogProxy("domain-a"),
            "domain-b": FogProxy("domain-b"),
        }

    def issue_ssi(self, wallet: SSIWallet, metadata: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "did": wallet.did,
            "metadata": metadata,
            "attributes": sorted(wallet.attributes),
            "subject_pk": pem_public_key(wallet.public_identity_key),
            "issued_by": "hospital-issuer",
        }
        signature = sign_payload(self.aa.master_signing_key, payload)
        wallet.credential = payload
        wallet.vc_signature = signature
        for attribute in wallet.attributes:
            wallet.attribute_private_keys[attribute] = self.aa.issue_attribute_private_key(attribute)
        self.ledger.credentials[wallet.did] = {"credential": payload, "signature": signature}
        self.ledger.record_event("ssi_issued", {"did": wallet.did})
        return {"credential": payload, "signature": signature}

    def validate_credential(self, wallet: SSIWallet) -> bool:
        if not wallet.credential or not wallet.vc_signature:
            return False
        return verify_signature(self.aa.master_signing_key.public_key(), wallet.credential, wallet.vc_signature)

    def generate_proof(
        self,
        user: DataUser,
        did: str,
        ipfs_hash: str,
        nonce: str,
    ) -> Dict[str, Any]:
        commitment_input = canonical_json(
            {"did": did, "ipfs_hash": ipfs_hash, "nonce": nonce, "attrs": sorted(user.wallet.attributes)}
        )
        if user.trustiness == "suspicious":
            engine = "zk-stark"
            witness_nonce = secrets.token_bytes(16)
            commitment = sha256_hex(commitment_input + witness_nonce)
            artifact = {
                "engine": engine,
                "commitment": commitment,
                "witness_nonce": b64(witness_nonce),
                "shares": additive_shares(sha256_bytes(commitment_input + witness_nonce)),
            }
        else:
            engine = "plonk"
            proof_digest = sha256_hex(commitment_input)
            artifact = {
                "engine": engine,
                "proof": proof_digest,
                "shares": additive_shares(sha256_bytes(commitment_input)),
            }
        proof_id = str(uuid.uuid4())
        self.ledger.proofs[proof_id] = {"artifact": artifact, "input": commitment_input}
        self.ledger.record_event("proof_generated", {"proof_id": proof_id, "engine": artifact["engine"]})
        return {"proof_id": proof_id, **artifact}

    def verify_proof(self, proof_bundle: Dict[str, Any]) -> bool:
        proof_id = proof_bundle["proof_id"]
        stored = self.ledger.proofs[proof_id]
        artifact = stored["artifact"]
        proof_input = stored["input"]
        if artifact["engine"] == "zk-stark":
            expected = sha256_hex(proof_input + b64d(artifact["witness_nonce"]))
            return expected == artifact["commitment"]
        expected = sha256_hex(proof_input)
        return expected == artifact["proof"]

    def precompute_policy(self, policy: PolicyNode) -> Dict[str, Any]:
        ordered = policy.ordered()
        minimal_sets = [sorted(item) for item in ordered.minimal_satisfying_sets()]
        attribute_map = {attr: sha256_hex(attr.encode("utf-8")) for attr in sorted(ordered.all_attributes())}
        return {
            "ordered_policy": ordered,
            "attribute_map": attribute_map,
            "minimal_sets": minimal_sets,
            "root_kind": ordered.kind,
        }

    def encrypt_record(
        self,
        owner: DataOwner,
        plaintext: bytes,
        policy: PolicyNode,
        metadata: Dict[str, Any],
    ) -> StoredRecord:
        rv = secrets.token_bytes(32)
        rv1, rv2 = split_bytes(rv)
        ctm = aesgcm_encrypt(rv, plaintext, aad=owner.wallet.did.encode("utf-8"))
        precomputed = self.precompute_policy(policy)
        ctrv1 = self._cpabe_style_encrypt(rv1, precomputed["minimal_sets"])
        record_id = f"record-{uuid.uuid4()}"
        payload = {
            "record_id": record_id,
            "ctm": ctm,
            "ctrv1": ctrv1,
            "rv2": b64(rv2),
            "owner_did": owner.wallet.did,
            "metadata": metadata,
        }
        proxy_b = self.domain_proxies["domain-b"]
        proxy_a = self.domain_proxies["domain-a"]
        shared = proxy_b.private_key.exchange(proxy_a.public_key)
        transport_key = derive_aes_key(shared, record_id.encode("utf-8"))
        proxy_payload = aesgcm_encrypt(transport_key, canonical_json(payload), aad=record_id.encode("utf-8"))
        merkle_leaf = canonical_json(
            {
                "record_id": record_id,
                "cid": sha256_hex(b64d(ctm["ciphertext"])),
                "owner_did": owner.wallet.did,
                "policy_digest": sha256_hex(canonical_json(precomputed["minimal_sets"])),
                "timestamp": metadata["timestamp"],
            }
        )
        tree = MerkleTree.build([merkle_leaf])
        self.ledger.merkle_roots[record_id] = tree.root
        self.ledger.record_event("record_encrypted", {"record_id": record_id})
        return StoredRecord(
            record_id=record_id,
            ctm=ctm,
            ctrv1=ctrv1,
            proxy_payload=proxy_payload,
            merkle_leaf=merkle_leaf,
            merkle_root=tree.root,
            merkle_proof=tree.proof(0),
            owner_did=owner.wallet.did,
            policy_root_kind=precomputed["root_kind"],
        )

    def _cpabe_style_encrypt(self, rv1: bytes, minimal_sets: List[List[str]]) -> Dict[str, Any]:
        envelopes = []
        for required_attrs in minimal_sets:
            ephemeral_private = x25519.X25519PrivateKey.generate()
            shared_parts = []
            for attribute in required_attrs:
                shared_parts.append(
                    ephemeral_private.exchange(self.aa.attribute_public_key(attribute))
                )
            key = derive_aes_key(*sorted(shared_parts), canonical_json(required_attrs))
            wrapped = aesgcm_encrypt(key, rv1, aad=canonical_json(required_attrs))
            envelopes.append(
                {
                    "attrs": required_attrs,
                    "ephemeral_pub": pem_x25519_public_key(ephemeral_private.public_key()),
                    "wrapped_rv1": wrapped,
                }
            )
        return {"envelopes": envelopes}

    def authenticate_and_retrieve(
        self,
        user: DataUser,
        stored: StoredRecord,
    ) -> bytes:
        if not self.validate_credential(user.wallet):
            raise ValueError("credential validation failed")
        if not MerkleTree.verify(stored.merkle_leaf, stored.merkle_proof, stored.merkle_root):
            raise ValueError("merkle verification failed")
        proof_bundle = self.generate_proof(
            user=user,
            did=user.wallet.did,
            ipfs_hash=sha256_hex(stored.merkle_leaf),
            nonce=stored.record_id,
        )
        if not self.verify_proof(proof_bundle):
            raise ValueError("zk proof verification failed")
        proxy_b = self.domain_proxies["domain-b"]
        proxy_a = self.domain_proxies["domain-a"]
        shared = proxy_a.private_key.exchange(proxy_b.public_key)
        proxy_payload = self._unwrap_proxy_payload(stored, shared)
        return self._decrypt_payload(user, stored, proxy_payload)

    def _decrypt_payload(self, user: DataUser, stored: StoredRecord, proxy_payload: Dict[str, Any]) -> bytes:
        for envelope in stored.ctrv1["envelopes"]:
            if not set(envelope["attrs"]).issubset(user.wallet.attributes):
                continue
            ephemeral_pub = load_x25519_public_key(envelope["ephemeral_pub"])
            shared_parts = []
            for attr in envelope["attrs"]:
                shared_parts.append(user.wallet.attribute_private_keys[attr].exchange(ephemeral_pub))
            attribute_key = derive_aes_key(*sorted(shared_parts), canonical_json(envelope["attrs"]))
            rv1 = aesgcm_decrypt(attribute_key, envelope["wrapped_rv1"], aad=canonical_json(envelope["attrs"]))
            rv = rv1 + b64d(proxy_payload["rv2"])
            return aesgcm_decrypt(rv, stored.ctm, aad=stored.owner_did.encode("utf-8"))
        raise ValueError("no satisfying attribute set found for CP-ABE-style decryption")

    def _unwrap_proxy_payload(self, stored: StoredRecord, transport_shared: bytes) -> Dict[str, Any]:
        payload_bytes = aesgcm_decrypt(
            derive_aes_key(transport_shared, stored.record_id.encode("utf-8")),
            stored.proxy_payload,
            aad=stored.record_id.encode("utf-8"),
        )
        return json.loads(payload_bytes)

    def build_transport_for_record(self, stored: StoredRecord) -> StoredRecord:
        proxy_b = self.domain_proxies["domain-b"]
        proxy_a = self.domain_proxies["domain-a"]
        _ = self._unwrap_proxy_payload(stored, proxy_b.private_key.exchange(proxy_a.public_key))
        return stored


def example_policy() -> PolicyNode:
    return PolicyNode.op(
        "AND",
        PolicyNode.op("MOFN", PolicyNode.leaf("cardiology"), PolicyNode.leaf("researcher"), PolicyNode.leaf("licensed"), threshold=2),
        PolicyNode.op("OR", PolicyNode.leaf("hospital-a"), PolicyNode.leaf("emergency")),
    )
