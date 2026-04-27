from __future__ import annotations

from .protocol import DataOwner, DataUser, SSIWallet, SSLXIoMTSystem, example_policy

def main() -> None:

    system = SSLXIoMTSystem()

    owner_wallet = SSIWallet(

        did="did:example:owner-001",

        attributes={"cardiology", "hospital-a", "licensed"},

    )

    user_wallet = SSIWallet(

        did="did:example:user-002",

        attributes={"cardiology", "researcher", "hospital-a"},

    )

    owner = DataOwner(owner_id="owner-001", wallet=owner_wallet)

    user = DataUser(user_id="user-002", wallet=user_wallet, trustiness="verified")

    system.issue_ssi(owner.wallet, {"role": "patient", "domain": "hospital-a"})

    system.issue_ssi(user.wallet, {"role": "researcher", "domain": "hospital-b"})

    policy = example_policy()

    record = system.encrypt_record(

        owner=owner,

        plaintext=b"cross-domain EHR payload",

        policy=policy,

        metadata={"timestamp": "2025-05-14T00:00:00Z", "cid": "ipfs://ehr-001"},

    )

    recovered = system.authenticate_and_retrieve(user, record)

    print(recovered.decode("utf-8"))

if __name__ == "__main__":

    main()
