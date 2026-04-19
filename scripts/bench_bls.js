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
    return `mean=${s.mean.toFixed(3)}ms  std=${s.std.toFixed(3)}ms`;
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
    const { secretKey, publicKey } = blsl.keygen();
    const messages = [], hashed = [];
    for (let i = 0; i < n; i++) {
        const buf = Buffer.alloc(40);
        buf.writeUInt32BE(0x53435045, 0); buf.writeUInt32BE(i, 4);
        crypto.randomFillSync(buf, 8, 32);
        messages.push(new Uint8Array(buf)); hashed.push(blsl.hash(new Uint8Array(buf)));
    }

    const signStats = await timeRun(async () => blsl.sign(hashed[0], secretKey), RUNS_PER_OP, WARMUP);
    const sigs = hashed.map(h => blsl.sign(h, secretKey));
    const aggStats = await timeRun(async () => blsl.aggregateSignatures(sigs), RUNS_PER_OP, WARMUP);
    const aggSig = blsl.aggregateSignatures(sigs);

    const G1Generator = bls12_381.G1.Point.BASE;
    let Q_agg = hashed[0];
    for (let i = 1; i < n; i++) Q_agg = Q_agg.add(hashed[i]);

    const pairingOnlyStats = await timeRun(async () => {
        const lhs = bls12_381.pairing(G1Generator, aggSig);
        const rhs = bls12_381.pairing(publicKey, Q_agg);
        if (String(lhs) !== String(rhs)) throw new Error("pairing fail");
    }, RUNS_PER_OP, WARMUP);

    const inputs = hashed.map(h => ({ message: h, publicKey }));
    const verifyAggStats = await timeRun(async () => blsl.verifyBatch(aggSig, inputs), RUNS_PER_OP, WARMUP);

    const naiveRuns = Math.max(5, Math.floor(RUNS_PER_OP / Math.max(1, Math.log10(n) * 3)));
    const verifyNaiveStats = await timeRun(async () => {
        for (let i = 0; i < n; i++) blsl.verify(sigs[i], hashed[i], publicKey);
    }, naiveRuns, WARMUP);

    return { n, sign: signStats, aggregate: aggStats, pairing_only: pairingOnlyStats, verify_agg: verifyAggStats, verify_naive: verifyNaiveStats };
}

(async () => {
    console.error("Generating fresh BLS Data and saving to CSV...");
    const results = [];
    for (const n of BATCH_SIZES) results.push(await benchBatchSize(n));

    const resultsDir = path.join(ROOT, "results");
    if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });
    const csvPath = path.join(resultsDir, "bls_bench.csv");
    
    let rows = "timestamp,batch_size,operation,n_runs,mean_ms,std_ms,median_ms,min_ms,max_ms\n";
    const ts = new Date().toISOString();
    for (const r of results) {
        for (const op of ["sign", "aggregate", "pairing_only", "verify_agg", "verify_naive"]) {
            const s = r[op];
            rows += `${ts},${r.n},${op},${s.n},${s.mean.toFixed(4)},${s.std.toFixed(4)},${s.median.toFixed(4)},${s.min.toFixed(4)},${s.max.toFixed(4)}\n`;
        }
    }
    fs.writeFileSync(csvPath, rows);
    console.error("CSV Saved successfully!");
})();
