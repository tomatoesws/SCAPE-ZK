# SSL-XIoMT Executable Reference

This folder is a runnable, paper-aligned re-implementation of the six SSL-XIoMT phases described in:

`SSL-XIoMT: Secure, Scalable, and Lightweight Cross-Domain IoMT Sharing With SSI and ZKP Authentication`

It is designed to stay faithful to the paper's architecture without fabricating performance values.

## What This Implements

The code covers the full end-to-end protocol flow:

1. System initialization
2. SSI generation and credential validation
3. Adaptive ZKP authorization path selection
4. Data encryption
5. Policy pre-computation before pairing-style evaluation
6. Cross-domain transfer, integrity verification, and decryption

The implementation includes:

- DID + verifiable credential issuance with ECDSA signatures
- Local and consortium-ledger style validation
- Adaptive proof engine selection:
  - suspicious users -> `zk-stark`
  - previously verified users -> `plonk`
- MPC-style additive sharing for proof material handling
- Merkle tree construction and proof verification
- AES-GCM payload encryption
- X25519-based cross-domain proxy exchange
- CP-ABE-style access control using policy trees and attribute key material
- Ordered gate pre-computation with `AND > MofN > OR`

## Important Accuracy Boundary

This is a faithful executable reference, not a claim that every low-level primitive exactly matches the unpublished implementation details behind the paper.

The paper provides system phases and pseudocode, but it does not fully publish:

- exact SSI wallet/ACA-Py workflow internals
- concrete ZK-STARK and PLONK circuit definitions
- MPC protocol transcript details
- complete CP-ABE parameterization beyond the pseudocode level
- full numeric series for all performance plots

Accordingly:

- protocol structure follows the paper
- paper-reported numbers are stored separately and illustrated without interpolation
- engineering choices needed to make the code runnable are treated as implementation assumptions, not paper measurements

## Files

- [`protocol.py`](/home/slotty666/researchpaper/paper/ssl_xiomt/protocol.py): main executable model
- [`paper_metrics.py`](/home/slotty666/researchpaper/paper/ssl_xiomt/paper_metrics.py): source-tagged paper facts only
- [`generate_paper_figures.py`](/home/slotty666/researchpaper/paper/ssl_xiomt/generate_paper_figures.py): SVG illustrations from explicit paper values only
- [`demo.py`](/home/slotty666/researchpaper/paper/ssl_xiomt/demo.py): runnable end-to-end scenario
- [`tests/test_ssl_xiomt.py`](/home/slotty666/researchpaper/paper/tests/test_ssl_xiomt.py): protocol checks

## Run

```sh
PYTHONPATH=/home/slotty666/researchpaper/paper python3 -m ssl_xiomt.demo
PYTHONPATH=/home/slotty666/researchpaper/paper python3 -m ssl_xiomt.generate_paper_figures
PYTHONPATH=/home/slotty666/researchpaper/paper python3 -m unittest tests.test_ssl_xiomt
```

## Paper-Sourced Numbers Included Here

Only explicit values extracted from the paper text are illustrated:

- proof generation + verification at `<= 1000` proofs:
  - Scheme `[31]`: `522.3 s`
  - Scheme `[29]`: `109.7 s`
  - SSL-XIoMT: `69.4-76.8 s`
- integrity throughput peak:
  - SSL-XIoMT: `918 verifications/s`
  - Scheme `[31]`: `777 verifications/s`
- integrity throughput crossover: SSL-XIoMT surpasses Scheme `[31]` after `> 50` concurrent requests
- integrity latency crossover: SSL-XIoMT outperforms Scheme `[31]` when requests exceed `500`
- secure cross-domain transmission: all compared schemes finish in `< 0.1 s`

No missing table cells or point-by-point plot data are invented here.
