# ALLCODE Directory - SCAPE-ZK Implementation Files

This directory contains a flattened collection of all source code, configuration files, and scripts from the SCAPE-ZK project. Each file is prefixed with a category identifier to show its original location in the project structure.

## File Organization

Files are organized by prefix into the following categories:

### 1. Network & Blockchain Setup (`01_run_commands_and_network__`)

These files configure and manage the Hyperledger Fabric network for the SCAPE-ZK evaluation.

| File | Purpose |
|------|---------|
| `01_run_commands_and_network__benchmark.sh` | Main script to run blockchain benchmarks on the Fabric network |
| `01_run_commands_and_network__bring-up-4peer.sh` | Brings up a 4-peer Hyperledger Fabric test network with 2 organizations |
| `01_run_commands_and_network__crypto-config-org1.yaml` | Cryptography configuration for organization 1 |
| `01_run_commands_and_network__crypto-config-org2.yaml` | Cryptography configuration for organization 2 |
| `01_run_commands_and_network__docker-compose-peer1.yaml` | Docker Compose configuration for peer nodes |

**How to use:** Run the network setup script first to initialize the Fabric network, then use the benchmark script to run performance tests.

### 2. Chaincode Implementation (`02_chaincode__`)

The Go implementations of SCAPE-ZK smart contracts for Hyperledger Fabric.

| File | Purpose |
|------|---------|
| `02_chaincode__scape_zk.go` | Main SCAPE-ZK chaincode implementation with proof verification and authorization logic |
| `02_chaincode__perf_test.go` | Performance test suite for local chaincode testing without network overhead |

**How to use:** Deploy `scape_zk.go` to the Fabric network. Use `perf_test.go` for quick performance validation during development.

### 3. Caliper Workload Configuration (`03_caliper_workload__`)

Hyperledger Caliper benchmark configuration files for measuring blockchain performance.

| File | Purpose |
|------|---------|
| `03_caliper_workload__benchmark.yaml` | Base Caliper configuration defining the benchmark workload |
| `03_caliper_workload__benchmark-operations.yaml` | Detailed transaction operations (submit/query) for benchmarking |
| `03_caliper_workload__network.yaml` | Network topology and peer/orderer definitions for Caliper |

**How to use:** These files define what operations Caliper will measure. Use them with the `benchmark.sh` script for repeatable performance testing.

### 4. Baseline Implementations (Prefix: `baselines__`)

Python implementations of baseline schemes for comparison against SCAPE-ZK.

| File | Purpose |
|------|---------|
| `baselines__common.py` | Shared utilities and common functions used by all baselines |
| `baselines__scheme30.py` | Implementation of Scheme 30 (a comparison baseline) |
| `baselines__sslxiomt.py` | SSL-XIoMT baseline implementation |
| `baselines__xauth.py` | XAuth baseline implementation |
| `baselines__subbaselines.py` | Additional sub-baseline implementations |
| `baselines____init__.py` | Python package initialization |
| `baselines____main__.py` | Entry point for baseline evaluation |

**How to use:** Run baseline simulations to generate comparison data. These implementations show how other schemes perform against SCAPE-ZK.

### 5. Benchmark Scripts

#### Cryptographic Primitives Benchmarks

| File | Purpose |
|------|---------|
| `bench_primitives.js` | JavaScript benchmarks for cryptographic primitives (BLS, curves, hashing) |
| `bench_bls.js` | Specific benchmarks for BLS signature scheme |
| `bench_snarkjs.js` | Benchmarks for snarkjs zero-knowledge proof operations |

#### Python Crypto Benchmarks

| File | Purpose |
|------|---------|
| `bench_cpabe.py` | CP-ABE (Ciphertext-Policy Attribute-Based Encryption) benchmarks |
| `bench_merkle.py` | Merkle tree operation benchmarks |
| `bench_pre.py` | PRE (Proxy Re-Encryption) benchmarks |
| `bench_missing_primitives.py` | Benchmarks for other cryptographic primitives |
| `bench_integrity_by_filesize.py` | Integrity verification performance by file size |
| `bls_bench.py` | Python BLS signature benchmarks |

#### Simulation & Analysis

| File | Purpose |
|------|---------|
| `baseline_sim.py` | Baseline simulation framework for performance analysis |
| `demo.py` | Quick demonstration script for SCAPE-ZK operations |
| `e2e_harness.py` | End-to-end test harness for full system testing |
| `e2e_harness_v2.py` | Updated version of the end-to-end test harness |

**How to use:** Run individual benchmark scripts to measure cryptographic performance. Use `demo.py` for quick testing and `e2e_harness.py` for comprehensive validation.

### 6. Analysis & Plotting Scripts

| File | Purpose |
|------|---------|
| `comparison_plots.py` | Generates comparative performance graphs between schemes |
| `compare_plots.py` | Additional plot comparison utilities |

**How to use:** Run these after collecting benchmark data to generate publication-ready figures.

### 7. Configuration Files

#### Fabric Configuration
- `configtx.yaml` - Fabric channel and consortium configuration
- `crypto-config.yaml` - Complete cryptographic material configuration
- `crypto-config-orderer.yaml` - Orderer organization crypto configuration
- `crypto-config-org1.yaml` & `crypto-config-org2.yaml` - Organization crypto configurations

#### Caliper Configuration
- `benchmark.yaml` - Main benchmark definition
- `benchmark-operations.yaml` - Operation details for benchmarking
- `benchmark-operations-txlog.yaml` - Transaction log configuration

#### Docker Compose
- `docker-compose.yaml` - Docker Compose for Fabric nodes
- `docker-compose.ipfs.yml` - Optional IPFS integration for data storage

**How to use:** These are typically used by the network setup and benchmark scripts. Modify if you need custom network topology or different operations.

## File Naming Convention

Files follow this pattern:
```
[NUMBER]_[CATEGORY]__[FILENAME]
```

- **NUMBER**: Order/dependency (01, 02, 03, etc.)
- **CATEGORY**: What subsystem it belongs to (run_commands_and_network, chaincode, caliper_workload, etc.)
- **FILENAME**: Original filename from the structured directory

**Examples:**
- `01_run_commands_and_network__benchmark.sh` → Original: `network/scripts/benchmark.sh`
- `02_chaincode__scape_zk.go` → Original: `chaincode/scape-zk/scape_zk.go`
- `03_caliper_workload__benchmark.yaml` → Original: `network/config/benchmark.yaml`

## Quick Reference Guide

### To Set Up & Run Benchmarks
1. Review network configuration files (01_*)
2. Run the network setup: `01_run_commands_and_network__bring-up-4peer.sh`
3. Deploy chaincode: Use `02_chaincode__scape_zk.go`
4. Configure Caliper: Review `03_caliper_workload__*.yaml` files
5. Run benchmarks: `01_run_commands_and_network__benchmark.sh`

### To Benchmark Cryptographic Primitives
1. Run JavaScript benchmarks: `node bench_primitives.js`
2. Run Python benchmarks: `python3 bench_cpabe.py`, `python3 bench_merkle.py`, etc.
3. Generate comparison plots: `python3 comparison_plots.py`

### To Compare Against Baselines
1. Review baseline implementations in `baselines__*.py`
2. Run baseline simulation: `python3 baseline_sim.py`
3. Generate comparison results: Check output CSV/JSON files
4. Visualize: `python3 compare_plots.py`

## Prerequisites

Before using these files, install:

- **Node.js** 18+ with npm
- **Python** 3.10+ with pip and venv
- **Go** 1.20+
- **Hyperledger Fabric** (if running blockchain tests)
- **Hyperledger Caliper** (if running distributed benchmarks)
- **circom** and **snarkjs** (for circuit compilation)
- **Docker** (for containerized Fabric network)

## Important Notes

- The `02_chaincode__*.go` files should be placed in `chaincode/scape-zk/` in the Fabric network
- Configuration files (*.yaml) may need path adjustments depending on your environment
- Scripts (*.sh) assume a Fabric test-network structure - verify paths before running
- Python scripts require the virtual environment: `source .venv/bin/activate`
- Some optional benchmarks (CP-ABE, PRE) may require additional dependencies

## File Dependencies

```
Network Setup (01_*) 
    ↓
Chaincode Deployment (02_*)
    ↓
Caliper Configuration (03_*)
    ↓
Benchmark Execution
    ↓
Analysis & Plotting
```

## Support & Troubleshooting

- Check that all dependencies are installed: `npm -v`, `python3 --version`, `go version`
- Verify Docker is running if using Fabric: `docker --version`
- Check file permissions if scripts fail to execute: `chmod +x *.sh`
- Review error logs from benchmark runs for specific failures
- See the parent `README.md` for additional project documentation

---

**Last Updated:** April 2026  
**Project:** SCAPE-ZK Research Prototype  
**Component:** Unified Code Distribution
