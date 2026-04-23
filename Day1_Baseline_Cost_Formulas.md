# Cost Formulas and Performance Data from Cryptography Papers

## XAuth: Efficient Privacy-Preserving Cross-Domain Authentication

### A. Computation Cost Formulas

XAuth uses a Zero-Knowledge Proof (ZKP) algorithm based on Pinocchio (PGHR13). The cost is primarily in the anonymous authentication protocol phase.

**Anonymous Authentication Protocol Computation Costs** (from Table 2):

| Function | Equations | Generate Proof | Proof Size | Verify |
|----------|-----------|-----------------|-----------|--------|
| V_Signature | 142,945 | 22.3s | 288 bytes | 9 ms |
| V_Validity | 244,626 | 39.7s | 288 bytes | 9 ms |
| V_SCT | 232,715 | 29.4s | 288 bytes | 9 ms |
| V_Nym | 17,405 | 2.7s | 288 bytes | 9 ms |
| **Total** | **614,286** | **89.7s** | **288 bytes** | **9 ms** |

**Key computation phases:**
- **Proof Generation**: Includes certificate verification (CertV), pseudonym verification (NymV)
  - CertV consists of: SubjectV (subject verification) + SigV (signature verification) + CRL verification + SCT verification
  - NymV: g^s * r^0 * g^r^1 == Nym_N (verification equation)
  
- **Proof Verification**: Linear in number of operations in validation function F
  - Total cost for anonymous proof verification: ~9 ms per user

**Operation Notation** (implied from implementation):
- Not explicitly defined in paper, but uses standard ZKP operations and pairing-based cryptography operations

### B. Communication Overhead / Message Size Formulas

**Anonymous Authentication Message Sizes:**
- Proof transmission size: 288 bytes (constant per user)
- Certificate operation size (leaf node): 125 bytes
- MMHT structure overhead (for storage):

| Number of Leaf Nodes | Leaf Node Size | MMHT Size | Root Size |
|---------------------|-----------------|-----------|-----------|
| 4 | 125 bytes | 503 bytes | 64 bytes |
| 8 | 125 bytes | 1,007 bytes | 64 bytes |
| 16 | 125 bytes | 1.97 KB | 64 bytes |
| 32 | 125 bytes | 3.95 KB | 64 bytes |
| 64 | 125 bytes | 7.92 KB | 64 bytes |
| 128 | 125 bytes | 15.8 KB | 64 bytes |

**Formula for MMHT Size**: Size increases exponentially with number of leaf nodes (approximately 8 * n + overhead)

### C. Storage Cost Formulas

**Per-Certificate Operation Storage Cost:**
- Single certificate operation: 125 bytes
- MMHT root hash: 64 bytes
- Total storage format includes: Data + DataType + Timestamp + Address + CheckTime + Extension
- Blockchain address w size: minimal (256-bit hash)

**Overall storage**: Exponential in number of certificates due to MMHT structure

### D. Concrete Values Reported (Experimental Data)

**Data Storage Phase:**
- Time to anchor MMHT in blockchain: 1.3 seconds (constant)
- Time spent in IPFS: ~23 ms
- Total storage time for complete process: < 2 seconds

**Data Inquiry Phase:**
- XAuth inquiry time: ~1.32 seconds (constant, not affected by number of certificates)
- BCTRT comparison: increases exponentially with number of certificates

**Data Recovery Phase:**
- Linear relationship with data size
- Time for recovering MMHT with 128 leaf nodes: ~0.7 seconds

**Data Control Protocol (Fast Collection and Binding):**
- Time to bind 128 certificate operations: 3.2 ms
- Average time per certificate operation: 25 ms

**Lightweight Correctness Validation:**
- BCTRT verification time per certificate: 13.52 ms
- XAuth verification time per certificate: 5 ms
- Improvement: Reduces verification latency by ~63%

### E. Baseline Comparisons

**Comparison schemes:**
- BCTRT [10]: Z.Wang et al., "Blockchain-based certificate transparency and revocationtransparency"
- CertChain [8]: J.Chen et al., "Certchain: Public and efficient certificate audit based on blockchain"
- CertLedger [9]: M.Y.Kubilay et al., "Certledger: An new PKI model with certificate transparency based on blockchain"

**Quantitative comparisons:**
- BCTRT: exponential growth in inquiry time with increasing certificates
- XAuth: constant ~1.32s inquiry time regardless of certificate count
- Verification speedup: XAuth achieves ~63% faster verification (5ms vs 13.52ms per certificate)

### F. Hardware / Test Setup

**Implementation Details:**
- CPU: Intel Core i7-6500U @ 2.5 GHz
- RAM: 8 GB
- OS: Ubuntu 16.04
- Blockchain: Ethereum (v1.8.4), communicated via Web3 API
- IPFS: version 0.5.0-dev
- Cryptographic library: OpenSSL (v1.1.1)
- Runtime: Node.js (v8.17.0)
- Hash algorithm: SHA-256
- ZKP implementation: Pinocchio (PGHR13)
- Prototype system: 5 security domains, each with at least one CA

**Curves/Primitives:**
- Pairing-based cryptography (not specified which elliptic curve)

---

## SSL-XIoMT: Secure, Scalable, and Lightweight Cross-Domain IoMT Sharing With SSI and ZKP Authentication

### A. Computation Cost Formulas

The scheme integrates ZK-STARK and PLONK protocols with Multi-Party Computation (MPC).

**Key computational phases:**

**Phase 1: SSI Generation**
- Algorithm: Cross-Domain-Auth-SSI()
- Functions: authIdentityIssue(), credentialIssue(), credentialValidation()
- MPC operations distribute cryptographic computations across nodes

**Phase 2: ZKP Proof Generation and Verification**
- For suspicious users (no prior history): ZK-STARK proof generation
- For verified users: PLONK proof generation and verification
- Off-chain proof pre-computation and zk-Rollup aggregation to minimize on-chain computation

**Algorithm 2: Optimized ZKP-Proof Generation With MPC and zk-Rollups:**
```
nonce ← MPC.Rand(RV)
commitment ← MPC.Hash(polyno(s,pc) + nonce)
if trustiness is suspicious then
    Store(commitment, nonce) off-chain
else
    proof ← MPC.Hash(s + polyno(s,pc))
    Store proof off-chain
return commitment or proof
```

**Algorithm 3: Optimized ZKP-Proof Verification:**
```
if batching then
    batched_proofs ← zk-Rollup.Extract(proof)
    return MPC.VerifyBatch(batched_proofs, srs)
else
    return MPC.Verify(proof, srs)
```

**Phase 3: CP-ABE Encryption with Pre-computation**

**Algorithm 5: Fog-Node Encryption with Pre-computation:**
```
hybridPrecomputeResults = hybridPreComputePairing(g, h, f, attributes)
CT_RV1 = CP-ABE-Encrypt(RV1, PK, PolicyTree, hybridPrecomputeResults)
```

**Algorithm: HYBRID_PRE (Pre-computation Before Pairing):**
```
e_gg, e_gh, e_gf = pair(g,g), pair(g,h), pair(g,f)
att_map = {attr: H.h(attr,G1) for attr in atts}
dynamic_params = dynamicOptimization()
return (e_gg, e_gh, e_gf, attribute_map, dynamic_params)
```

**Operation Notation:**
- MPC operations: Multi-Party Computation distributed across nodes
- zk-Rollup.Aggregate(): Batch multiple proofs off-chain
- pair(x,y): Bilinear pairing operation
- H.h(attr,G1): Hash-to-G1 mapping

### B. Communication Overhead / Message Size Formulas

**Data Transmission Across Domains** (from Table 3):

The paper reports combined performance of three key functions:
1. Setup (PKI key generation and parameter initialization)
2. ECC-based encryption (secures payload under public/private key pairs)
3. IPFS-based integrity verification (distributed hash verification)

**Concrete transmission measurements:**
- System consistently achieved lowest overall latency
- All schemes completed end-to-end processing under 0.1 seconds
- Communication overhead measured across domain boundaries

**Message components:**
- DID (Decentralized Identifier): variable size
- Verifiable Credential (VC): variable size
- ZKP proof commitments: off-chain or batched via zk-Rollups
- ECC-encrypted payload: data-size dependent

### C. Storage Cost Formulas

Storage overhead is distributed across:
1. On-chain: Minimal (only proof hashes via Hyperledger)
2. Off-chain: Proof pre-computations and zk-Rollup aggregates
3. IPFS storage: Encrypted IoMT data

Not explicitly quantified in paper with mathematical formulas, but qualitatively:
- Off-chain storage reduces on-chain bloat
- IPFS provides distributed storage without blockchain overhead

### D. Concrete Values Reported (Experimental Data)

**Proof Generation and Verification Performance:**

When simulating up to 10,000 ZKP proofs:
- Scheme [31] (standard ZK-SNARK): 522.3 seconds (≤1000 proofs)
- Scheme [29] (at-zkp): ~109.7 seconds
- SSL-XIoMT (PLONK + ZK-STARK): 69.4–76.8 seconds

At 5,000–10,000 proofs:
- Scheme [31] outpaced Scheme [29] but still lagged behind SSL-XIoMT

**Encryption Performance:**

Attribute-based encryption (constant data size 10,000 KB, variable attributes):
- SSL-XIoMT achieved fastest encryption time across all attribute sizes
- Scheme [29] (DABE): highest computation cost
- Scheme [31]: moderate performance
- Attribute counts below 160: comparable performance between [31] and SSL-XIoMT
- Attribute counts up to 300: SSL-XIoMT maintained significantly lower encryption latency
- Improvement due to pre-computation for attribute mapping and logical gate optimization

**Decryption Performance:**
- SSL-XIoMT outperformed both baselines
- Linear improvement over Scheme [31]
- Significantly faster than Scheme [29]

**Secure Data Transmission:**
- Setup phase: cryptographic parameter generation and randomness initialization
- ECC-based encryption: secures payload under public/private key pairs
- IPFS integrity verification: distributed hash checks
- All schemes completed end-to-end processing in < 0.1 seconds
- SSL-XIoMT showed best overall performance with faster execution across all steps

**Integrity Verification and Throughput:**

Merkle Tree verification with IPFS hashing:
- At 500+ concurrent requests: SSL-XIoMT outperforms Scheme [31]
- Under minimal load (<50): Scheme [31] slightly lower latency
- Peak throughput: 918 verifications/second (100–150 users) for SSL-XIoMT
- Scheme [31] maximum: 777 verifications/second

### E. Baseline Comparisons

**Comparison schemes:**
- Scheme [27]: Wang et al., FABRIC - cross-domain proxy re-encryption
- Scheme [28]: Xiong et al., Revocable ABE with digital twins
- Scheme [29]: Xiong et al., Attribute-based data sharing for autonomous transportation
- Scheme [31]: Wang et al., Blockchain-based secure cross-domain data sharing
- Scheme [32]: Dai et al., HAPPS - hidden attribute privilege protection

**Key functional comparison metrics** (Table 2):
- SSI support: Yes (complete)
- ZKP flexibility: Yes (hybrid PLONK + ZK-STARK)
- Post-quantum resistance: Yes (ZK-STARK)
- Pre-compute pairing: Yes (optimized)
- Lightweight IoMT: Yes
- Merkle integrity checks: Yes

Schemes [27], [28], [30], [31]: Missing one or more of the above capabilities

**Quantitative improvements:**
- Proof generation/verification: 9–10% faster than Scheme [31] at 1000 proofs
- Encryption time: Significantly lower (exact %) across all attribute sizes
- Decryption latency: Consistently outperforms baselines
- Throughput: 918 vs 777 verifications/second (18% improvement)

### F. Hardware / Test Setup

**Server Configuration:**
- CPU: Intel Xeon E-2336 @ 2.9 GHz
- RAM: 16 GB
- OS: Ubuntu 20.04

**Implementation:**
- Language: Python
- Cryptographic libraries: PyCryptodome, Charm-Crypto, OpenSSL
- CP-ABE: Docker-CP-ABE and pairing-operation libraries
- ZKP implementation: Rust libraries (libstark, bellman)
- Identity management: Hyperledger Aries Cloud Agent Python (ACA-Py)

**Curves/Primitives:**
- Elliptic curves: Not explicitly named (implied modern curves)
- Pairing types: Not specified
- Hash function: Standard cryptographic hashes

**Blockchain/Distributed System:**
- Hyperledger: Consortium blockchain
- IPFS: InterPlanetary File System for distributed storage
- Consensus: Protocol not specified in excerpt

---

## Scheme [30]: Cross-Domain Identity Authentication Scheme for IIoT Identification Resolution System Based on Self-Sovereign Identity

### A. Computation Cost Formulas

The scheme leverages attribute-based signature technology, aggregate signatures, and bilinear pairings.

**Key cryptographic operations** (from Table V - Computation Comparison):

**Operation Notation:**
- E₁: Exponentiation operations in group G₁ or G₂
- E₂: Multiplication operations in group G₁ or G₂
- e: Bilinear pairing operations
- |π|: Number of secrets in zero-knowledge proof

**Computational Phases:**

**ShowCred Phase (Credential Presentation):**
Cost depends on:
- n_I: number of issuers
- n_k: number of disclosed attributes
- n_i: number of attributes each issuer can authorize
- Linear operations in elliptic curve multiplication (relatively small computation change)

When n_I (number of issuers) is fixed at 10 and n_k (disclosed attributes) varies 10–50:
- Ma et al. [31]: constant cost
- Fuchsbauer et al. [13]: constant cost
- Shi et al. [14]: linear decreasing trend
- Hébant & Pointcheval [32]: linear increasing trend (minor increase, elliptic curve multiplication)
- Su et al. [27]: linear increasing trend
- Scheme [30]: linear increasing trend (minor increase, comparable to elliptic curve ops)

When n_k is fixed at 10 and n_I varies 5–40:
- Ma et al. [31]: constant cost
- Su et al. [27]: constant cost
- Scheme [30]: constant cost
- Fuchsbauer et al. [13]: linear increasing trend
- Shi et al. [14]: linear increasing trend

**Verify Phase (Verification):**
Cost depends on n_k (disclosed attributes) and n_I (number of issuers).
Similar patterns to ShowCred, with all curves showing linear increase as n_k increases from 10 to 50.

**Trace Phase (User Tracking):**
Cost varies with audit node threshold:
- Shi et al. [14]: linear increase with threshold (requires traversing user lists)
- Hébant & Pointcheval [32]: independent of threshold (but practically requires user list traversal)
- Scheme [30]: Direct computation of user's public key, lower traversal overhead

**Update Phase (Credential Updates):**
Cost increases with number of updated credentials:
- Issuer computational cost: linear increase with number of credential updates
- User computational cost: linear increase, but relatively low (elliptic curve multiplication dominant operation)

**Batch Authentication Phase:**
When number of authenticated users increases from 1 to 50:
- Batch authentication: significantly smaller rate of increase vs non-batch
- Improvement: 62.5% to 92.79% optimization in authentication phase costs

### B. Communication Overhead / Message Size Formulas

**Storage Overhead** (Table IV - Storage Comparison):

**Primitive sizes:**
- |G₁|: size of element in group G₁
- |G₂|: size of element in group G₂
- |G_T|: size of element in target group G_T
- |Z_p|: size of element in Z_p (modular integers)

**Key pair size variations:**
- Ma et al. [31]: constant (single-attribute authority)
- Shi et al. [14]: linear in total number of attributes n_a
- Su et al. [27]: linear in number of issuers n_I
- Other schemes: linear in number of attributes each issuer can authorize

**Credential sizes:**
- Ma et al. [31]: constant (single-attribute scenario)
- Shi et al. [14]: related to number of issuers
- Fuchsbauer et al. [13]: related to number of issuers
- Hébant & Pointcheval [32]: related to total number of attributes n_a
- Su et al. [27]: related to total number of attributes n_a
- Scheme [30]: constant-sized credentials (comparable to other multi-issuer schemes)

**Credential presentation sizes:**
- Fuchsbauer et al. [13]: size related to n_I (number of issuers)
- Su et al. [27]: size related to number of attributes
- Ma et al. [31], Shi et al. [14], Hébant & Pointcheval [32], Scheme [30]: constant size

**Communication Overhead** (Fig. 11(b) - Authentication Phase):

When total attributes fixed at 50 and number of issuers fixed at 5:
- Ma et al. [31]: requires multiple zero-knowledge proofs (high cost)
- Su et al. [27]: cannot selectively disclose attributes (requires all credentials)
- Fuchsbauer et al. [13]: requires credentials from all relevant issuers (high cost)
- Scheme [30]: optimized communication
  - Optimization: 62.5% to 92.79% reduction in communication cost during authentication
  - Enables selective attribute disclosure and batch authentication

### C. Storage Cost Formulas

**Overall storage cost characteristics:**

When number of issuers is fixed at 5:
- Storage cost increases with number of authorized attributes
- Scheme [30] storage cost increases but remains within acceptable range
- Benefits from constant-size credentials and efficient attribute encoding

**Comparison:**
- Ma et al. [31], Shi et al. [14], Fuchsbauer et al. [13]: storage costs remain unchanged with attribute variations
- All other schemes (including Scheme [30]): storage scales with attributes but at practical rates

### D. Concrete Values Reported (Experimental Data)

**ShowCred Phase Time Costs** (Fig. 7):

When n_I = 10, n_i = 10, n_T = 5:
- Cost increases with n_k (disclosed attributes 10–50)
- Rate of increase: relatively small due to elliptic curve multiplication dominance
- Example: ~linear increase as n_k grows

When n_k = 10, n_i = 5, n_T = 5:
- Cost remains constant or shows minimal increase when n_I varies 5–40
- Fuchsbauer et al. [13]: significant linear increase
- Shi et al. [14]: linear increase
- Scheme [30]: constant cost

**Verify Phase Time Costs** (Fig. 8):

Similar patterns to ShowCred:
- n_I constant (10), n_k varies (10–50): linear increase for most schemes
- n_k constant (10), n_i varies (5–40): constant cost for Scheme [30], linear for others

**Trace Phase Time Costs** (Fig. 9(a)):

When audit node threshold increases:
- Shi et al. [14]: significant time increase (traverses user lists, computes task recovery)
- Hébant & Pointcheval [32]: independent of threshold (approximately constant, ~practical overhead for list traversal)
- Scheme [30]: direct public key computation, lower overhead than Shi et al. [14]

**Credential Update Phase Time Costs** (Fig. 9(b)):

As number of updated credentials increases (from ~1 to multiple):
- Issuer cost: linear increase
- User cost: linear increase but relatively low (elliptic curve multiplication operations)

**Batch vs Non-batch Authentication** (Fig. 10):

When number of authenticated users increases from 1 to 50:
- Batch authentication: smaller rate of increase
- Non-batch authentication: faster rate of increase
- Scheme [30] demonstrates significant efficiency gains with batch authentication
- Improvement: as users increase, batch mode maintains computational efficiency

**Storage Overhead** (Fig. 11(a)):

When number of issuers fixed at 5:
- Hébant & Pointcheval [32], Su et al. [27], Scheme [30]: increase with authorized attributes
- Ma et al. [31], Shi et al. [14], Fuchsbauer et al. [13]: unchanged
- Scheme [30] storage remains within acceptable range despite attribute scaling

**Communication Overhead** (Fig. 11(b)):

Fixed at 50 total attributes, 5 issuers:
- Ma et al. [31]: high (multiple ZKP requirements)
- Su et al. [27]: high (cannot selectively disclose)
- Fuchsbauer et al. [13]: high (requires all issuer credentials)
- Scheme [30]: 62.5%–92.79% optimization

### E. Baseline Comparisons

**Comparison schemes:**

**Anonymous credential schemes:**
- Ma et al. [31]: Single-attribute authority
- Shi et al. [14]: Threshold tracking, URS with zero-knowledge proofs
- Hébant & Pointcheval [32]: DSqDH assumption, user tracking
- Fuchsbauer et al. [13]: Selective attribute disclosure
- Su et al. [27]: Aggregate Anonymous Key Issuing (AAKI), access control tree

**Key functional comparison** (Table III):
- Features assessed: relationship between attributes (R), selective disclosure (S), access control tree (A), zero-knowledge proof (ZKP), unlinkable ring signature (URS), aggregatable signature with randomizable tags (ART-Sign), structure-preserving signature (SPS-EQ), access control tree (TREE)

**Quantitative advantages of Scheme [30]:**
- Threshold-based identity tracking and revocation
- Attribute credential updates mechanism
- Batch authentication support
- Communication optimization: 62.5%–92.79% reduction
- Storage efficiency: constant-sized credentials with multi-issuer support
- Computational efficiency: constant cost in many scenarios vs linear for others

**Limitations of baseline schemes:**
- Shi et al. [14]: requires multiple attribute authorities to jointly participate (poor adaptability); linear increasing trend in computation
- Hébant & Pointcheval [32]: only supports tracking (no revocation); computational overhead increases linearly
- Fuchsbauer et al. [13]: requires different credentials for independent authentication; higher communication overhead
- Su et al. [27]: limitations in randomization, identity revocation, attribute credential updates
- Ma et al. [31]: single-attribute authority, limited functionality

### F. Hardware / Test Setup

**Simulation Environment:**

**Computer Specifications:**
- CPU: 12th Gen Intel(R) Core(TM) i7-12700H @ 2.30 GHz
- RAM: 32 GB
- OS: Windows 11

**Cryptographic Implementation:**

**Pairing library:**
- PBC library (Pairing-Based Cryptography library)
- Type-III pairings (specifically typeF curve)

**Cryptographic operations:**
- Python-based pairing encryption package built on PBC library
- Assumes all schemes use zero-knowledge proofs based on Schnorr protocol
- Type-3 pairings used throughout (Pointcheval-Sanders signature protocol)

**Test parameters:**
- Number of issuers: n_I = 5–40 (in various tests)
- Attributes per issuer: n_i = 5–10
- Disclosed attributes: n_k = 10–50
- Tracking nodes: n_T = 5
- Threshold nodes: t_T = 3
- Number of users: 10 (for credential update phase)
- Number of authenticated users: 1–50 (for batch authentication tests)

**Blockchain Deployment** (Section D):

- Blockchain platform: FISCO BCOS (consortium blockchain)
- Network topology: 6-node consortium blockchain with group-based architecture
- Consensus algorithm: PBFT (Practical Byzantine Fault Tolerance)
- Network communication: P2P network for data synchronization and consistency

**Curves/Primitives:**

- Elliptic curve pairings: Type-III pairings (typeF curve)
- Signature scheme: Pointcheval-Sanders (PS) signature
  - Group operations: G₁, G₂ groups with bilinear pairing e: G₁ × G₂ → G_T
  - Secret key: sk = (x, y) where x, y ∈ Z_p*
  - Public key: pk = (X, Y) = (g₂^x, g₂^y)
  - Signature length: 2 elements (σ₁, σ₂)

**Key cryptographic operations used:**
- Bilinear pairings: e(σ₁, X·Y^m) = e(σ₂, g₂)
- Hash functions: standard cryptographic hash
- Zero-knowledge proofs: based on Schnorr protocol with Fiat-Shamir heuristic

---

## Summary Comparison Across Three Papers

| Aspect | XAuth | SSL-XIoMT | Scheme [30] |
|--------|-------|-----------|-----------|
| **Primary Authentication Method** | ZKP (Pinocchio PGHR13) | ZKP (PLONK + ZK-STARK) + SSI + MPC | Attribute-based signature + ZKP |
| **Computation Model** | Centralized proof computation | Distributed MPC + off-chain computation | Multi-issuer attribute-based |
| **Key Performance Metric** | Proof verification (9 ms) | Proof generation/verification (69–77 sec for 10k proofs) | Batch authentication (62–93% optimization) |
| **Communication Proof Size** | 288 bytes | Variable (batched off-chain) | Constant-sized credentials |
| **Storage Scaling** | Exponential (MMHT) | Linear (off-chain) | Linear (attribute-dependent) |
| **Baseline Comparison** | BCTRT: 13.52 ms vs 5 ms | Scheme [31]: 522 sec vs 69–77 sec | Fuchsbauer et al.: high comm vs 62–93% optimization |
| **Hardware** | Intel i7-6500U, 2.5 GHz, 8GB | Intel Xeon E-2336, 2.9 GHz, 16GB | Intel i7-12700H, 2.3 GHz, 32GB |

