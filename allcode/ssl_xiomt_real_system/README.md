# SSL-XIoMT Real System Blueprint

This folder captures the actual SSL-XIoMT system described in:

`SSL-XIoMT_Secure_Scalable_and_Lightweight_Cross-Domain_IoMT_Sharing_With_SSI_and_ZKP_Authentication (2).pdf`

The goal here is to document the paper-defined end-to-end system faithfully, without inventing runtime numbers or pretending that the full stack already exists in this workspace.

## Paper Identity

- Title: `SSL-XIoMT: Secure, Scalable, and Lightweight Cross-Domain IoMT Sharing With SSI and ZKP Authentication`
- DOI: `10.1109/OJCS.2025.3570087`
- Received: `2025-04-17`
- Accepted: `2025-05-11`
- Published: `2025-05-14`
- Current version: `2025-06-02`

## Real System Components From The Paper

Section III.A defines these entities:

1. Data Owner (DO)
2. Data Users (DUs)
3. Fog Node with proxy server
4. Hyperledger consortium blockchain
5. Local blockchain in each domain
6. IPFS in each domain/hospital
7. SSI wallet

The paper also relies on:

- DID + verifiable credentials for identity
- Hyperledger for smart contracts and traceability
- ZK-STARK for suspicious or previously unseen users
- PLONK for already verified users
- MPC for privacy-preserving credential/proof handling
- zk-Rollups for batching proofs off-chain before on-chain verification
- CP-ABE for policy-based access control
- PRE-style re-encryption before sharing
- Merkle-tree integrity verification
- AES for data encryption
- ECC-based secure exchange for part of the key transfer path

## Real End-To-End Flow From The Paper

The paper's Section III.B breaks the system into six phases.

1. System Initialization
AA distributes keys/attributes for DO, DU, issuer, proxy, and IPFS-side participants.

2. SSI Generation
Hospitals issue DID-based verifiable credentials and store/validate them through Hyperledger smart contracts. MPC is used to distribute sensitive identity computations.

3. ZKP Authentication and Authorization
The system selects the proof path based on trust level:
- suspicious/new user: `ZK-STARK`
- verified user: `PLONK`

Proofs are prepared off-chain, optionally batched with zk-Rollups, and verified via smart contracts.

4. Data Encryption
The DO encrypts the EHR with AES and splits the AES key into `RV1` and `RV2`.
- `RV1` is protected with CP-ABE
- `RV2` is used in ECC-based secure exchange

The fog proxy performs the heavier CP-ABE work.

5. Pre-Computation Before Pairing
The fog node pre-computes attribute mapping and reorders policy-tree logic before pairing. The paper explicitly prioritizes gate evaluation as:

`AND > MofN > OR`

This is claimed to reduce unnecessary traversal and pairing cost.

6. Data Decryption / Retrieval
The DU performs local and cross-domain authentication, presents VC + ZKP, passes Merkle-based integrity checks, receives securely transferred ciphertext/key material, reconstructs the AES key from `RV1` and `RV2`, then decrypts the EHR.

## What Makes This A "Full System" In The Paper

The paper is not only a ZKP benchmark or a CP-ABE benchmark. Its claimed full system combines:

- identity issuance and validation
- adaptive cross-domain authentication
- authorization with hybrid ZKPs
- blockchain-backed verification and logging
- offloaded CP-ABE encryption/decryption
- proxy-assisted cross-domain transfer
- integrity verification with Merkle proofs and IPFS hashes
- final EHR decryption by the authorized requester

That is the architecture illustrated in [ssl_xiomt_real_system.svg](/home/slotty666/researchpaper/paper/ssl_xiomt_real_system/ssl_xiomt_real_system.svg).

## Real Reported Evaluation Facts

These are values stated in the paper text, not invented locally.

- Test environment:
  - `Ubuntu 20.04`
  - `Intel Xeon E-2336 @ 2.9 GHz`
  - `16 GB RAM`
  - Python implementation
  - `PyCryptodome`, `Charm-Crypto`, `OpenSSL`
  - `Docker-CP-ABE`, `pairing-operation`
  - Rust libraries `libstark`, `bellman`
  - Hyperledger `ACA-Py`

- Proof generation + verification:
  - simulated up to `10,000` ZKPs
  - when proofs were `<= 1000`:
    - Scheme `[31]`: `522.3 seconds`
    - Scheme `[29]`: about `109.7 seconds`
    - SSL-XIoMT: about `69.4-76.8 seconds`

- Integrity verification throughput:
  - SSL-XIoMT surpasses Scheme `[31]` after more than `50` concurrent requests
  - peak reported SSL-XIoMT throughput: `918 verifications/second` at `100-150 users`
  - peak reported Scheme `[31]` throughput: `777 verifications/second`

- Cross-domain secure transmission:
  - the paper states all compared schemes completed the end-to-end process in under `0.1 seconds`

## Numbers Intentionally Not Invented Here

The paper includes figures and a `Table 3` for cross-domain transmission sub-steps, but the extracted text available in this workspace does not expose the table cells cleanly. This folder therefore does not manufacture per-step values for:

- setup time in Table 3
- ECC encryption time in Table 3
- IPFS integrity-check time in Table 3
- exact point-by-point values from Figures 4, 5, and 6

If those exact table cells are needed, the next step is manual transcription or OCR from the PDF page itself.

## Local Workspace Status

This workspace does **not** currently contain a runnable full SSL-XIoMT implementation matching the paper.

What exists locally:

- Hyperledger/Fabric network and chaincode scaffolding:
  - [paper/network/fabric-test-network](</home/slotty666/researchpaper/paper/network/fabric-test-network>)
  - [paper/chaincode/scape-zk/scape_zk.go](/home/slotty666/researchpaper/paper/chaincode/scape-zk/scape_zk.go)

- ZK/circuit material:
  - [paper/circuits](</home/slotty666/researchpaper/paper/circuits>)

- Benchmark scripts and result CSVs:
  - [paper/scripts](</home/slotty666/researchpaper/paper/scripts>)
  - [paper/results](</home/slotty666/researchpaper/paper/results>)

What is still missing for a true paper-faithful SSL-XIoMT stack:

1. SSI wallet + DID/VC issuance and revocation service
2. ACA-Py driven issuer/verifier flows integrated with the blockchain
3. Actual adaptive `PLONK` vs `ZK-STARK` proof pipeline
4. MPC-based credential/proof handling
5. IPFS-backed encrypted object storage wired into retrieval
6. PRE and ECC exchange path integrated with CP-ABE key recovery
7. End-to-end orchestration across at least two domains

## Practical Interpretation

If the requirement is "use the real SSL-XIoMT system and do not make up numbers," the correct position is:

- use the paper's architecture as the source of truth
- only cite values the paper explicitly reports
- clearly separate local benchmark-derived estimates from paper-reported measurements
- do not label the current SCAPE-ZK/Fabric code as a full SSL-XIoMT implementation

