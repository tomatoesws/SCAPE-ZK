# Section 7.C / 7.D - Blockchain Scalability and Deployment

## 7.C On-chain Scalability

To evaluate the blockchain layer of SCAPE-ZK, we deployed the Go chaincode on a local Hyperledger Fabric consortium network and measured operation-specific throughput and latency with Hyperledger Caliper. The test network used four peers across two organizations, one ordering service, channel `scapechannel`, and chaincode `scapezk`. Each chaincode operation was evaluated at 100, 500, and 1000 submitted transactions. We first executed one warm-up run and excluded it from the reported statistics. The full benchmark was then repeated ten times, and all reported values are the mean and sample standard deviation across these ten logged trials.

The benchmark covers the ledger-facing operations exposed by the SCAPE-ZK chaincode: `Register`, `VerifyProof`, `Revoke`, `UpdateCred`, and `RecordExists`. The first four operations mutate ledger state, while `RecordExists` is a read-only query used to check whether a credential or authorization record has already been anchored. Across the ten repeated trials, all 15 benchmark rounds completed successfully and no failed transactions were observed.

At the 1000-transaction load, the state-mutating operations achieved closely grouped throughput. `Register` reached 215.15 +/- 14.24 TPS, `VerifyProof` reached 221.19 +/- 8.03 TPS, `Revoke` reached 221.20 +/- 13.61 TPS, and `UpdateCred` reached 221.56 +/- 10.47 TPS. The read-only `RecordExists` operation achieved substantially higher throughput, 702.38 +/- 38.86 TPS, because it avoids the endorsement, validation, and world-state update costs associated with write transactions. This separation between read and write performance is consistent with the intended SCAPE-ZK ledger design: expensive cryptographic work is performed off-chain, while the blockchain stores compact authorization, revocation, and audit state.

Latency remained low at the 1000-transaction load. The average latencies of `Register`, `VerifyProof`, `Revoke`, and `UpdateCred` were 0.089 +/- 0.012 s, 0.087 +/- 0.007 s, 0.086 +/- 0.008 s, and 0.092 +/- 0.008 s, respectively. `RecordExists` completed in 0.010 +/- 0.000 s on average. These results show that, under the tested local consortium configuration, the Fabric deployment can sustain hundreds of SCAPE-ZK ledger write operations per second while keeping average write latency below 0.1 s at the highest tested load.

The repeated trials also show stable scaling as the offered load increases. For write operations, throughput was approximately 19-20 TPS at 100 transactions, approximately 131 TPS at 500 transactions, and approximately 215-222 TPS at 1000 transactions. `RecordExists` increased from 112.98 +/- 1.41 TPS at 100 transactions to 447.05 +/- 15.10 TPS at 500 transactions and 702.38 +/- 38.86 TPS at 1000 transactions. Since every submitted transaction succeeded across the repeated benchmark set, the measured throughput increase was not obtained by sacrificing reliability under the tested load range.

The reported `VerifyProof` result should be interpreted as a blockchain-layer transaction benchmark. In the current prototype, Fabric chaincode records a proof-verification or authorization result as ledger state; it does not execute full Groth16 or BLS verification inside chaincode. Therefore, the `VerifyProof` latency reported here captures proposal endorsement, ordering, validation, commit, and ledger-update costs for recording the verification result. End-to-end verification latency includes the off-chain cryptographic proof generation and verification path in addition to the Fabric transaction latency measured in this subsection.

Recommended figure placement:

- Throughput at 1000 transactions: `figures/repeated-throughput-1000tx.svg`
- Average latency at 1000 transactions: `figures/repeated-latency-1000tx.svg`
- Throughput across 100, 500, and 1000 transactions: `figures/repeated-throughput-by-load.svg`
- Success/failure summary: `figures/repeated-success-summary.svg`

## 7.D Blockchain Deployment

SCAPE-ZK was deployed on Hyperledger Fabric because the target cross-domain healthcare setting is naturally permissioned. Hospitals, clinics, laboratories, insurers, and regulators can be modeled as consortium participants with known identities, rather than anonymous public-chain accounts. Fabric provides membership management, endorsement policies, channel isolation, deterministic chaincode execution, and auditable ledger state, all of which are useful for regulated data-sharing environments.

The deployed prototype used a four-peer Fabric network with two organizations and one ordering service. The SCAPE-ZK smart contract was implemented as Go chaincode and exposes functions for registering credential metadata, recording authorization or proof-verification outcomes, revoking credentials, updating credential state, and querying record existence. As a result, the deployment evaluates the cost of anchoring compact SCAPE-ZK state transitions on a permissioned blockchain. Each submitted write transaction follows the standard Fabric path of proposal endorsement, ordering, validation, and commit to the world state.

This deployment model keeps the blockchain role deliberately compact. Zero-knowledge proof generation, aggregate-signature processing, CP-ABE encryption, and proxy re-encryption are performed by off-chain clients or service components. Fabric is then used to record compact outputs and state transitions, including credential registration, verification decisions, revocation visibility, and audit evidence. This division reduces the amount of computation placed inside chaincode while preserving the benefits of a shared ledger: consistency across domains, tamper-evident authorization state, and auditable updates.

The deployment results complement the analytical scalability comparison in the paper, but they should not be read as a direct TPS comparison against XAuth, SSL-XIoMT, or Scheme [30]. A direct numeric comparison would require implementing each competing system in the same Fabric/Caliper environment, under the same endorsement policy, transaction mix, hardware, and load profile. The contribution of this experiment is instead to show that the SCAPE-ZK blockchain interface can run repeatedly on a realistic permissioned ledger stack with zero failed transactions in the tested workload.

Overall, the blockchain experiment supports the practical deployment claim of SCAPE-ZK: the system can keep heavy cryptographic operations off-chain while using a consortium ledger for compact authorization state, revocation, consistency, and auditability. Full end-to-end deployment evaluation should combine the off-chain cryptographic timings with the Fabric transaction path measured here.
