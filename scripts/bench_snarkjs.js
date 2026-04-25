const snarkjs = require("snarkjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");

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
    const median = sorted[Math.floor(n / 2)];
    const min = sorted[0];
    const max = sorted[n - 1];
    return { n, mean, std, median, min, max };
}

function fmt(s) {
    return `mean=${s.mean.toFixed(2)}ms  std=${s.std.toFixed(2)}ms  ` +
           `median=${s.median.toFixed(2)}ms  min=${s.min.toFixed(2)}ms  max=${s.max.toFixed(2)}ms  (n=${s.n})`;
}

async function benchCircuit(name, runs, warmup) {
    const wasmPath = path.join(ROOT, "circuits", `${name}_js`, `${name}.wasm`);
    const inputPath = path.join(ROOT, "circuits", `input_${name}.json`);
    const zkeyPath = path.join(ROOT, "keys", `${name}_final.zkey`);
    const vkeyPath = path.join(ROOT, "keys", `${name}_vkey.json`);

    for (const p of [wasmPath, inputPath, zkeyPath, vkeyPath]) {
        if (!fs.existsSync(p)) {
            console.error(`Missing: ${p}`);
            process.exit(1);
        }
    }

    const input = JSON.parse(fs.readFileSync(inputPath, "utf8"));
    const vKey = JSON.parse(fs.readFileSync(vkeyPath, "utf8"));

    const proveTimes = [];
    const verifyTimes = [];

    console.error(`Benchmarking ${name}: ${runs} runs + ${warmup} warmup...`);

    for (let i = 0; i < runs + warmup; i++) {
        const t0 = hrMs();
        const { proof, publicSignals } =
            await snarkjs.groth16.fullProve(input, wasmPath, zkeyPath);
        const t1 = hrMs();

        const v0 = hrMs();
        const ok = await snarkjs.groth16.verify(vKey, publicSignals, proof);
        const v1 = hrMs();

        if (!ok) {
            console.error(`Run ${i}: VERIFICATION FAILED`);
            process.exit(2);
        }

        if (i >= warmup) {
            proveTimes.push(t1 - t0);
            verifyTimes.push(v1 - v0);
        }
        process.stderr.write(`.${i === runs + warmup - 1 ? "\n" : ""}`);
    }

    const pS = stats(proveTimes);
    const vS = stats(verifyTimes);

    console.error(`\n${name} — prove+witness: ${fmt(pS)}`);
    console.error(`${name} — verify:         ${fmt(vS)}`);

    const resultsDir = path.join(ROOT, "results");
    if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });
    const csvPath = path.join(resultsDir, "groth16_bench.csv");
    const isNew = !fs.existsSync(csvPath);
    const header = "timestamp,circuit,metric,n,mean_ms,std_ms,median_ms,min_ms,max_ms\n";
    const ts = new Date().toISOString();
    const rows =
        `${ts},${name},prove_fullprove,${pS.n},${pS.mean.toFixed(3)},${pS.std.toFixed(3)},${pS.median.toFixed(3)},${pS.min.toFixed(3)},${pS.max.toFixed(3)}\n` +
        `${ts},${name},verify,${vS.n},${vS.mean.toFixed(3)},${vS.std.toFixed(3)},${vS.median.toFixed(3)},${vS.min.toFixed(3)},${vS.max.toFixed(3)}\n`;
    fs.appendFileSync(csvPath, (isNew ? header : "") + rows);
    console.error(`Appended to ${csvPath}`);
}

(async () => {
    const name = process.argv[2] || "multiplier";
    const runs = parseInt(process.argv[3] || "10", 10);
    const warmup = parseInt(process.argv[4] || "2", 10);
    try {
        await benchCircuit(name, runs, warmup);
    } catch (e) {
        console.error("Error:", e);
        process.exit(3);
    } finally {
        process.exit(0);
    }
})();
