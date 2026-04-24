# Real Baseline Reproduction Plan

This note defines how to move from the current modeled baselines to actual
baseline-system reproductions for `XAuth [6]`, `SSL-XIoMT [8]`, and
`Scheme [30]`.

## Bottom Line

Right now the repository supports:

- `SCAPE-ZK`: actual local implementation and measurements
- `XAuth [6]`: paper-anchored model
- `SSL-XIoMT [8]`: paper-anchored model
- `Scheme [30]`: paper-anchored model with citation ambiguity

So if the goal is to claim "we implemented the real baselines", we are **not**
there yet.

## What "Real System" Should Mean

For each baseline, we should be able to point to:

1. the exact paper citation
2. the exact protocol stages we reproduced
3. the exact local code implementing those stages
4. the exact benchmark command that produced each reported result
5. the exact limitations where our reproduction is partial

## Recommended Strategy

Do **not** try to reproduce all three full papers at once. The papers combine
system architecture, storage, identity, and cryptographic layers, and some
claims are only available as final timing plots rather than directly executable
algorithms.

Instead, build a `minimal faithful benchmark` for each baseline.

That means:

- implement only the performance-critical path used for comparison
- preserve the paper's core primitive choices and message flow
- explicitly exclude unsupported subsystems
- report the result as `partial reproduction of the comparison-critical path`
  unless the whole system is actually rebuilt

## Per-Baseline Target

### 1. XAuth [6]

Target reproduction:

- certificate operation record format
- MMHT insertion and proof generation
- correctness validation flow
- anonymous-authentication proof and verification path

Likely blockers:

- original Pinocchio-era proof stack is not present in this repo
- blockchain and IPFS integration details are architectural, not benchmark-ready
- some timing claims are coarse-grained totals rather than per-operation traces

Recommended deliverable:

- `baselines/xauth/` implementation with a benchmark runner
- measured outputs for:
  - anonymous proof generation
  - anonymous proof verification
  - MMHT validation

### 2. SSL-XIoMT [8]

Target reproduction:

- a narrowed benchmark consisting of:
  - SSI credential object
  - one ZKP path
  - one CP-ABE path
  - one "batch verification" path

Likely blockers:

- the paper combines Hyperledger, SSI, MPC, PLONK, ZK-STARK, fog-node CP-ABE,
  and zk-rollup claims
- the full architecture is too broad to rebuild quickly and may require
  decisions the paper does not pin down precisely

Recommended deliverable:

- `baselines/ssl_xiomt/` with separately benchmarked modules
- each module clearly marked as:
  - `faithful`
  - `approximated`
  - `not reproduced`

### 3. Scheme [30]

Target reproduction:

- confirm the exact cited source first
- implement:
  - issuer setup
  - credential issuance
  - selective disclosure / presentation
  - verification

Likely blockers:

- current citation mapping is unclear in this repo
- the local `[30].pdf` appears to reference several comparator schemes rather
  than being the already-implemented baseline itself

Recommended deliverable:

- no implementation work until citation mapping is fixed

## Order Of Work

1. Confirm the exact bibliography for `[6]`, `[8]`, and `[30]`
2. Create one folder per baseline under `baselines/`
3. Write one `SPEC.md` per baseline listing:
   - paper claim
   - reproduced subset
   - excluded parts
   - benchmark metrics
4. Implement XAuth first
5. Implement SSL-XIoMT second as a modular partial reproduction
6. Implement Scheme [30] only after citation confirmation

## Claim Language To Use

Until the above is done, use wording like:

> XAuth, SSL-XIoMT, and Scheme [30] are currently paper-anchored modeled
> baselines in this repository, not full reproduced implementations.

After partial implementation, use:

> We reproduce the comparison-critical path of baseline X under the subset
> described in `baselines/<name>/SPEC.md`.
