# Baseline Reproduction Status

This directory tracks the transition from paper-anchored baseline modeling to
actual baseline-system reproduction.

## Scope

The target baselines used in this repository are:

- `XAuth [6]`
- `SSL-XIoMT [8]`
- `Scheme [30]`

## Current Reality

At the moment, this repository contains:

- local SCAPE-ZK circuit implementations and measurements
- paper-anchored simulators and formula-instantiated baseline values
- plots that compare SCAPE-ZK to baseline claims

It does **not** yet contain complete, faithful implementations of the three
baseline systems.

## Why This Matters

For the paper, there is a big difference between:

- `modeled comparison`: reproduce the paper's reported numbers by formulas,
  extracted constants, or calibrated primitive timings
- `reproduced system`: implement the actual protocol flow and measure it in our
  environment

Only the second one supports the claim that we ran the real baseline systems.

## Status Summary

See [manifest.json](/home/tomato/scape-zk/baselines/manifest.json:1) for the
machine-readable status and next steps for each baseline.
