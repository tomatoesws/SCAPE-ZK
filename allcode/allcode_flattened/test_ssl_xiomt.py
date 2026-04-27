from __future__ import annotations

import unittest

from ssl_xiomt.protocol import DataOwner, DataUser, PolicyNode, SSIWallet, SSLXIoMTSystem, example_policy

class SSLXIoMTTests(unittest.TestCase):

    def setUp(self) -> None:

        self.system = SSLXIoMTSystem()

        self.owner = DataOwner(

            owner_id="owner-001",

            wallet=SSIWallet(

                did="did:example:owner-001",

                attributes={"cardiology", "hospital-a", "licensed"},

            ),

        )

        self.user = DataUser(

            user_id="user-001",

            wallet=SSIWallet(

                did="did:example:user-001",

                attributes={"cardiology", "researcher", "hospital-a"},

            ),

            trustiness="verified",

        )

        self.system.issue_ssi(self.owner.wallet, {"role": "patient"})

        self.system.issue_ssi(self.user.wallet, {"role": "researcher"})

    def test_policy_ordering_prioritizes_and_then_mofn_then_or(self) -> None:

        policy = PolicyNode.op(

            "OR",

            PolicyNode.leaf("x"),

            PolicyNode.op("AND", PolicyNode.leaf("a"), PolicyNode.leaf("b")),

            PolicyNode.op("MOFN", PolicyNode.leaf("m1"), PolicyNode.leaf("m2"), threshold=1),

        )

        ordered = policy.ordered()

        self.assertEqual([child.kind for child in ordered.children], ["AND", "MOFN", "LEAF"])

    def test_verified_user_uses_plonk_path(self) -> None:

        proof = self.system.generate_proof(self.user, self.user.wallet.did, "ipfs-hash", "nonce-1")

        self.assertEqual(proof["engine"], "plonk")

        self.assertTrue(self.system.verify_proof(proof))

    def test_suspicious_user_uses_stark_path(self) -> None:

        suspicious = DataUser(

            user_id="user-002",

            wallet=SSIWallet(did="did:example:user-002", attributes={"licensed", "emergency"}),

            trustiness="suspicious",

        )

        self.system.issue_ssi(suspicious.wallet, {"role": "guest"})

        proof = self.system.generate_proof(suspicious, suspicious.wallet.did, "ipfs-hash", "nonce-2")

        self.assertEqual(proof["engine"], "zk-stark")

        self.assertTrue(self.system.verify_proof(proof))

    def test_end_to_end_retrieval(self) -> None:

        record = self.system.encrypt_record(

            owner=self.owner,

            plaintext=b"ehr",

            policy=example_policy(),

            metadata={"timestamp": "2025-05-14T00:00:00Z", "cid": "ipfs://ehr-001"},

        )

        recovered = self.system.authenticate_and_retrieve(self.user, record)

        self.assertEqual(recovered, b"ehr")

    def test_retrieval_fails_without_required_attributes(self) -> None:

        outsider = DataUser(

            user_id="user-003",

            wallet=SSIWallet(did="did:example:user-003", attributes={"emergency"}),

            trustiness="verified",

        )

        self.system.issue_ssi(outsider.wallet, {"role": "visitor"})

        record = self.system.encrypt_record(

            owner=self.owner,

            plaintext=b"ehr",

            policy=example_policy(),

            metadata={"timestamp": "2025-05-14T00:00:00Z", "cid": "ipfs://ehr-001"},

        )

        with self.assertRaises(ValueError):

            self.system.authenticate_and_retrieve(outsider, record)

if __name__ == "__main__":

    unittest.main()
