// SCAPE-ZK Phase 3 — BLS Aggregate Signature Benchmark v3
// Decomposes verify_agg to show the TRUE O(1) on-chain pairing cost

const { bls12_381 } = require("@noble/curves/bls12-381.js");
const blsl = bls12_381.longSignatures;
const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");

const ROOT = path.join(os.homedir(), "scape-zk");
const BATCH_SIZES = [1, 10, 50, 100, 200];
const RUNS_PER_OP = 20;
const WARMUP = 3;

function hrMs() {
    const [s, ns] = process.hrtime();
    return s * 1000 + ns / 1e6;
}

function stats(arr) {
    const n = arr.length;
    const mean = arr.reduce((a, b) => a + b, 0) / n;
    const variance = arr.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1 || 1);
    const std = Math.sqrt(variance);
    const sorted = [...arr].sort((a, b) => a - b);
    return { n, mean, std, median: sorted[Math.floor(n / 2)], min: sorted[0], max: sorted[n - 1] };
}

function fmt(s) {
    return `mean=${s.mean.toFixed(3)}ms  std=${s.std.toFixed(3)}ms  median=${s.median.toFixed(3)}ms`;
}

async function timeRun(fn, runs, warmup) {
    const times = [];
    for (let i = 0; i < runs + warmup; i++) {
        const t0 = hrMs();
        await fn();
        const t1 = hrMs();
        if (i >= warmup) times.push(t1 - t0);
    }
    return stats(times);
}

async function benchBatchSize(n) {
    console.error(`\n=== Batch size n = ${n} ===`);
    const { secretKey, publicKey } = blsl.keygen();

    const messages = [];
    const hashed = [];
    for (let i = 0; i < n; i++) {
        const buf = Buffer.alloc(40);
        buf.writeUInt32BE(0x53435045, 0);
        buf.writeUInt32BE(i, 4);
        crypto.randomFillSync(buf, 8, 32);
        const m = new Uint8Array(buf);
        messages.push(m);
        hashed.push(blsl.hash(m));
    }

    const signStats = await timeRun(async () => blsl.sign(hashed[0], secretKey), RUNS_PER_OP, WARMUP);
    console.error(`sign:           ${fmt(signStats)}`);

    const sigs = hashed.map(h => blsl.sign(h, secretKey));
    const aggStats = await timeRun(async () => blsl.aggregateSignatures(sigs), RUNS_PER_OP, WARMUP);
    console.error(`aggregate:      ${fmt(aggStats)}`);

    const aggSig = blsl.aggregateSignatures(sigs);

    // PAIRING-ONLY (Table V On-chain Cost)
    const G1Generator = bls12_381.G1.Point.BASE;
    let Q_agg = hashed[0];
    for (let i = 1; i < n; i++) {
        Q_agg = Q_agg.add(hashed[i]);
    }

    const pairingOnlyStats = await timeRun(
        async () => {
            const lhs = bls12_381.pairing(G1Generator, aggSig);
            const rhs = bls12_381.pairing(publicKey, Q_agg);
            // Hack for @noble/curves Fp12 object equality
            if (String(lhs) !== String(rhs)) throw new Error("pairing check failed");
        },
        RUNS_PER_OP, WARMUP
    );
    console.error(`pairing_only:   ${fmt(pairingOnlyStats)}  <-- ON-CHAIN O(1) Cost`);

    const inputs = hashed.map(h => ({ message: h, publicKey }));
    const verifyAggStats = await timeRun(async () => blsl.verifyBatch(aggSig, inputs), RUNS_PER_OP, WARMUP);
    console.error(`verify_agg:     ${fmt(verifyAggStats)}  <-- includes O(n) preprocessing`);

    const naiveRuns = Math.max(5, Math.floor(RUNS_PER_OP / Math.max(1, Math.log10(n) * 3)));
    const verifyNaiveStats = await timeRun(
        async () => {
            for (let i = 0; i < n; i++) blsl.verify(sigs[i], hashed[i], publicKey);
        },
        naiveRuns, WARMUP
    );
    console.error(`verify_naive:   ${fmt(verifyNaiveStats)}  <-- O(n) baseline`);

    return { n, pairing_only: pairingOnlyStats, verify_agg: verifyAggStats, verify_naive: verifyNaiveStats };
}

(async () => {
    console.error("SCAPE-ZK BLS Aggregate Signature Benchmark v3");
    
    // Sanity check
    const { secretKey, publicKey } = blsl.keygen();
    const m = blsl.hash(new TextEncoder().encode("sanity"));
    const s = blsl.sign(m, secretKey);
    if (!blsl.verify(s, m, publicKey)) throw new Error("sanity failed");

    const results = [];
    for (const n of BATCH_SIZES) {
        results.push(await benchBatchSize(n));
    }

    console.error("\n" + "=".repeat(85));
    console.error("KEY TABLE — pairing_only is the TRUE on-chain cost (should be flat)");
    console.error("=".repeat(85));
    console.error("batch  | pairing_only | verify_agg | verify_naive | naive/pairing | naive/verify_agg");
    console.error("-".repeat(85));
    for (const r of results) {
        const sp1 = r.verify_naive.mean / r.pairing_only.mean;
        const sp2 = r.verify_naive.mean / r.verify_agg.mean;
        console.error(
            `${String(r.n).padStart(5)}  | ` +
            `${r.pairing_only.mean.toFixed(2).padStart(11)} | ` +
            `${r.verify_agg.mean.toFixed(2).padStart(10)} | ` +
            `${r.verify_naive.mean.toFixed(2).padStart(12)} | ` +
            `${sp1.toFixed(1).padStart(12)}x | ` +
            `${sp2.toFixed(1).padStart(15)}x`
        );
    }
})();
