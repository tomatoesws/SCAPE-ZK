# Parameter Alignment for Fair Baseline Comparison

This note defines which baseline comparisons are valid under the same
workload parameters as SCAPE-ZK, and which ones should be treated as
paper-anchored estimates rather than exact parity experiments.

## SCAPE-ZK master workload

- Number of attributes: `{5, 10, 20, 50}`
- Number of disclosed attributes: `{2, 5, 10, 20}`
- Batch sizes / aggregate verification: `{1, 10, 50, 100, 200}`
- Number of issuers: `{1, 5, 10}`
- Number of concurrent users / requests: `{1, 10, 50, 100}`

## Baseline support matrix

### XAuth

- Proof generation anchor: `89,700 ms`
- Proof verification anchor: `9 ms / user`
- Shared workload dimensions with SCAPE-ZK:
  - concurrent users / requests: `yes`
- Not shared:
  - attributes
  - disclosed attributes
  - issuers
  - batch verification as SSI-style aggregate verification

Interpretation:
- Fair to compare against SCAPE-ZK on request-count / concurrent-user axes.
- Not fair to place XAuth on attribute-count or issuer-count plots.

### SSL-XIoMT

- Proof benchmark uses up to `10,000 proofs`
- Throughput benchmark discusses `50`, `100-150`, `500+`, `750+` users
- Encryption benchmark varies attribute counts, but the paper text refers to
  larger points such as `160` and `300`, not SCAPE-ZK's exact sweep.

Shared workload dimensions with SCAPE-ZK:
- concurrent users / requests: `partially yes`
- attributes: `conceptually yes, exact points no`

Not clearly shared:
- disclosed attributes
- issuers
- SCAPE-ZK-style batch verification

Interpretation:
- Fair to compare SSL-XIoMT on request-count / user-count axes.
- Attribute plots should be marked as approximate unless exact points are
  extracted or reproduced.

### Scheme [30]

From the extracted PDF text:
- disclosed attributes are fixed at `10` in one experiment and swept from
  `10` to `50` in another
- issuers are fixed at `10` in one experiment and swept from `5` to `20` in another
- batch-authenticated users are swept from `1` to `50`

Shared workload dimensions with SCAPE-ZK:
- disclosed attributes: `partially yes`
- issuers: `partially yes`
- batch-authenticated users: `partially yes`

Not clearly shared:
- SCAPE-ZK's direct attribute-count sweep `{5, 10, 20, 50}`

Interpretation:
- Best baseline for issuer and disclosure scaling.
- Fair to compare only on overlapping points and only if exact numeric values
  are extracted or reproduced.

## Practical plotting rules

### Exact-parity figures we can defend now

1. Proof cost vs requests per session:
   - SCAPE-ZK amortized
   - SCAPE-ZK request proof
   - XAuth
   - SSL-XIoMT
   - Shared x-axis: `{1, 10, 50, 100}`

2. Verification cost vs concurrent users:
   - SCAPE-ZK on-chain pairing verification
   - XAuth (`9 ms * n`)
   - SSL-XIoMT (`1000/918 ms * n`)
   - Shared x-axis: `{1, 10, 50, 100}`

### Figures that still need exact extraction or reproduction

1. Attribute-count comparison including SSL-XIoMT exact points
2. Disclosed-attribute comparison against Scheme [30]
3. Issuer-count comparison against Scheme [30]
4. Batch verification comparison against Scheme [30] using exact paper values

## Recommended wording

Use wording such as:

> We report exact-parity comparisons only on workload dimensions shared by all
> compared schemes. When a baseline paper does not expose the same parameter
> axis, we avoid direct matched-parameter plotting or explicitly mark the
> comparison as paper-anchored rather than reproduced.
