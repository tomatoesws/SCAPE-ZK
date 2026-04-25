#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { bls12_381 } = require("@noble/curves/bls12-381.js");

const ROOT = path.resolve(__dirname, "..");
const RESULTS_DIR = path.join(ROOT, "results");
const OPS_PER_RUN = 1000;
const TOTAL_RUNS = 11;
const WARMUP_RUNS = 1;
const MEASURED_RUNS = TOTAL_RUNS - WARMUP_RUNS;
const HASH_ALG = "sha256";
const HASH_INPUT_BYTES = 32;
const SYM_ALG = "aes-256-gcm";
const SYM_INPUT_BYTES = 1024;
const CURVE = "BLS12-381";
const SECURITY_LEVEL = "128-bit";

function hrMs() {
    return Number(process.hrtime.bigint()) / 1e6;
}

function mean(arr) {
    return arr.reduce((acc, x) => acc + x, 0) / arr.length;
}

function stddev(arr) {
    if (arr.length <= 1) return 0;
    const mu = mean(arr);
    const variance = arr.reduce((acc, x) => acc + (x - mu) ** 2, 0) / (arr.length - 1);
    return Math.sqrt(variance);
}

function stats(arr) {
    const sorted = [...arr].sort((a, b) => a - b);
    return {
        n: arr.length,
        mean: mean(arr),
        std: stddev(arr),
        min: sorted[0],
        max: sorted[sorted.length - 1],
        median: sorted[Math.floor(sorted.length / 2)],
    };
}

function fmtMs(x) {
    return `${x.toFixed(6)} ms`;
}

function safeCommand(cmd, args) {
    try {
        return execFileSync(cmd, args, { encoding: "utf8" }).trim();
    } catch (_) {
        return null;
    }
}

function machineInfo() {
    const cpuModel = safeCommand("bash", ["-lc", "lscpu | awk -F: '/Model name/ {gsub(/^ +/, \"\", $2); print $2; exit}'"]) ||
        (os.cpus()[0] ? os.cpus()[0].model : "unknown");
    const ram = safeCommand("bash", ["-lc", "free -h | awk '/Mem:/ {print $2}'"]) || `${(os.totalmem() / (1024 ** 3)).toFixed(1)} GiB`;
    const kernel = safeCommand("uname", ["-sr"]) || `${os.type()} ${os.release()}`;
    return {
        hostname: os.hostname(),
        cpu_model: cpuModel,
        cpu_cores_logical: os.cpus().length,
        ram_total: ram,
        os: kernel,
        node: process.version,
    };
}

function makeScalars(n) {
    const out = [];
    const order = bls12_381.fields.Fr.ORDER;
    for (let i = 0; i < n; i++) {
        const raw = crypto.randomBytes(32);
        const scalar = (BigInt(`0x${raw.toString("hex")}`) % (order - 1n)) + 1n;
        out.push(scalar);
    }
    return out;
}

function makeHashes(n) {
    const out = [];
    for (let i = 0; i < n; i++) {
        out.push(crypto.randomBytes(HASH_INPUT_BYTES));
    }
    return out;
}

function makePayloads(n, size) {
    const out = [];
    for (let i = 0; i < n; i++) {
        out.push(crypto.randomBytes(size));
    }
    return out;
}

function runBenchmark(name, op) {
    const perRunMs = [];
    let checksum = 0n;

    for (let run = 0; run < TOTAL_RUNS; run++) {
        const t0 = hrMs();
        const runChecksum = op();
        const t1 = hrMs();
        const avgPerOp = (t1 - t0) / OPS_PER_RUN;
        if (run >= WARMUP_RUNS) {
            perRunMs.push(avgPerOp);
        }
        checksum ^= BigInt(runChecksum);
    }

    return {
        name,
        checksum: checksum.toString(),
        per_run_ms: perRunMs,
        stats: stats(perRunMs),
    };
}

function benchHash() {
    const inputs = makeHashes(OPS_PER_RUN);
    return runBenchmark("Thash (SHA-256, 32B input)", () => {
        let acc = 0n;
        for (let i = 0; i < OPS_PER_RUN; i++) {
            const digest = crypto.createHash(HASH_ALG).update(inputs[i]).digest();
            acc ^= digest.readBigUInt64BE(0);
        }
        return acc;
    });
}

function benchGroupMul() {
    const scalars = makeScalars(OPS_PER_RUN);
    const base = bls12_381.G1.Point.BASE;
    return runBenchmark("Tgrp (BLS12-381 G1 scalar multiplication)", () => {
        let acc = 0n;
        for (let i = 0; i < OPS_PER_RUN; i++) {
            const point = base.multiply(scalars[i]);
            acc ^= point.toAffine().x;
        }
        return acc;
    });
}

function benchPairing() {
    const g1Scalars = makeScalars(OPS_PER_RUN);
    const g2Scalars = makeScalars(OPS_PER_RUN);
    const g1Base = bls12_381.G1.Point.BASE;
    const g2Base = bls12_381.G2.Point.BASE;
    const pairs = [];
    for (let i = 0; i < OPS_PER_RUN; i++) {
        pairs.push({
            p: g1Base.multiply(g1Scalars[i]),
            q: g2Base.multiply(g2Scalars[i]),
        });
    }

    return runBenchmark("Tpair (BLS12-381 bilinear pairing)", () => {
        let acc = 0n;
        for (let i = 0; i < OPS_PER_RUN; i++) {
            const gt = bls12_381.pairing(pairs[i].p, pairs[i].q);
            acc ^= gt.c0.c0.c0;
        }
        return acc;
    });
}

function benchSymmetric() {
    const payloads = makePayloads(OPS_PER_RUN, SYM_INPUT_BYTES);
    const key = crypto.randomBytes(32);
    const ivs = makePayloads(OPS_PER_RUN, 12);
    const aad = Buffer.from("scape-zk-primitive-bench");

    return runBenchmark("Tsym (AES-256-GCM, 1KB payload)", () => {
        let acc = 0n;
        for (let i = 0; i < OPS_PER_RUN; i++) {
            const cipher = crypto.createCipheriv(SYM_ALG, key, ivs[i]);
            cipher.setAAD(aad);
            const ct = Buffer.concat([cipher.update(payloads[i]), cipher.final()]);
            const tag = cipher.getAuthTag();
            acc ^= ct.readBigUInt64BE(0) ^ tag.readBigUInt64BE(0);
        }
        return acc;
    });
}

function printHeader(info) {
    console.log("Cryptographic Primitive Micro-benchmark");
    console.log("=======================================");
    console.log(`Security level          : ${SECURITY_LEVEL}`);
    console.log(`Pairing / group curve   : ${CURVE}`);
    console.log(`Hash                    : ${HASH_ALG.toUpperCase()}`);
    console.log(`Symmetric cipher        : ${SYM_ALG.toUpperCase()}`);
    console.log(`Operations per run      : ${OPS_PER_RUN}`);
    console.log(`Measured runs           : ${MEASURED_RUNS}`);
    console.log(`Warmup runs dropped     : ${WARMUP_RUNS}`);
    console.log("");
    console.log("Hardware / software");
    console.log("-------------------");
    console.log(`Host                    : ${info.hostname}`);
    console.log(`CPU                     : ${info.cpu_model}`);
    console.log(`Logical cores           : ${info.cpu_cores_logical}`);
    console.log(`RAM                     : ${info.ram_total}`);
    console.log(`OS                      : ${info.os}`);
    console.log(`Node.js                 : ${info.node}`);
    console.log("");
}

function printResult(result) {
    const s = result.stats;
    console.log(result.name);
    console.log(`  Average per op        : ${fmtMs(s.mean)}`);
    console.log(`  Std. dev. per op      : ${fmtMs(s.std)}`);
    console.log(`  Median per op         : ${fmtMs(s.median)}`);
    console.log(`  Min / max per op      : ${fmtMs(s.min)} / ${fmtMs(s.max)}`);
    console.log(`  Runs used             : ${s.n}`);
    console.log("");
}

function persist(info, results) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
    const stamp = new Date().toISOString();
    const jsonPath = path.join(RESULTS_DIR, "primitive_microbench.json");
    const csvPath = path.join(RESULTS_DIR, "primitive_microbench.csv");

    const payload = {
        timestamp: stamp,
        config: {
            security_level: SECURITY_LEVEL,
            curve: CURVE,
            hash: HASH_ALG,
            symmetric_cipher: SYM_ALG,
            hash_input_bytes: HASH_INPUT_BYTES,
            symmetric_input_bytes: SYM_INPUT_BYTES,
            ops_per_run: OPS_PER_RUN,
            total_runs: TOTAL_RUNS,
            warmup_runs_dropped: WARMUP_RUNS,
            measured_runs: MEASURED_RUNS,
        },
        machine: info,
        results: results.map((r) => ({
            primitive: r.name,
            checksum: r.checksum,
            per_run_ms: r.per_run_ms,
            stats: r.stats,
        })),
    };
    fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2));

    let csv = "timestamp,primitive,ops_per_run,measured_runs,mean_ms,std_ms,median_ms,min_ms,max_ms\n";
    for (const r of results) {
        const s = r.stats;
        csv += `${stamp},${JSON.stringify(r.name)},${OPS_PER_RUN},${s.n},${s.mean.toFixed(6)},${s.std.toFixed(6)},${s.median.toFixed(6)},${s.min.toFixed(6)},${s.max.toFixed(6)}\n`;
    }
    fs.writeFileSync(csvPath, csv);

    console.log("Saved artifacts");
    console.log("---------------");
    console.log(`JSON                    : ${jsonPath}`);
    console.log(`CSV                     : ${csvPath}`);
}

function main() {
    const info = machineInfo();
    printHeader(info);

    const results = [
        benchHash(),
        benchGroupMul(),
        benchPairing(),
        benchSymmetric(),
    ];

    console.log("Results");
    console.log("-------");
    for (const result of results) {
        printResult(result);
    }

    persist(info, results);
}

main();
