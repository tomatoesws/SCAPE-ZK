// Parameterized input generator: accepts attribute count as CLI arg
// Usage: node gen_inputs_n.js 20   → writes input_session_20.json

const { buildPoseidon, buildEddsa } = require("circomlibjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const NUM_ATTRS = parseInt(process.argv[2] || "10", 10);
const CHUNK = 14;  // must match session.circom

async function chunkedHash(poseidon, F, inputs) {
    if (inputs.length <= CHUNK) {
        return poseidon(inputs.map(x => F.e(x)));
    }
    // First chunk
    let acc = poseidon(inputs.slice(0, CHUNK).map(x => F.e(x)));
    // Subsequent chunks: Poseidon(acc, chunk_items...)
    for (let c = CHUNK; c < inputs.length; c += CHUNK) {
        const end = Math.min(c + CHUNK, inputs.length);
        const chunkItems = inputs.slice(c, end).map(x => F.e(x));
        acc = poseidon([acc, ...chunkItems]);
    }
    return acc;
}

async function main() {
    const poseidon = await buildPoseidon();
    const eddsa = await buildEddsa();
    const F = poseidon.F;
    const toStr = (x) => F.toObject(x).toString();

    const issuerPrv = Buffer.from("0001020304050607080900010203040506070809000102030405060708090001", "hex");
    const issuerPubPoint = eddsa.prv2pub(issuerPrv);

    const DID_DU = 12345678901234567890n;
    const attributes = [];
    for (let i = 0; i < NUM_ATTRS; i++) attributes.push(BigInt(100 + i));
    const t_exp = 2000000000n;
    const tau_now = 1700000000n;

    // Chunked VC hash
    const vcInputs = [DID_DU, ...attributes, t_exp];
    const vcHash = await chunkedHash(poseidon, F, vcInputs);

    const signature = eddsa.signPoseidon(issuerPrv, vcHash);

    const r = 987654321n;
    const C_VC = poseidon([vcHash, F.e(r)]);

    const expected_attrs = [...attributes];
    const psi = await chunkedHash(poseidon, F, expected_attrs);

    const sessionInput = {
        C_VC: toStr(C_VC),
        psi: toStr(psi),
        PK_Issuer_Ax: toStr(issuerPubPoint[0]),
        PK_Issuer_Ay: toStr(issuerPubPoint[1]),
        t_exp: t_exp.toString(),
        tau_now: tau_now.toString(),
        attributes: attributes.map(x => x.toString()),
        DID_DU: DID_DU.toString(),
        sig_R8x: toStr(signature.R8[0]),
        sig_R8y: toStr(signature.R8[1]),
        sig_S: signature.S.toString(),
        r: r.toString(),
        expected_attrs: expected_attrs.map(x => x.toString()),
    };

    const outPath = path.join(ROOT, "circuits", `input_session_${NUM_ATTRS}.json`);
    fs.writeFileSync(outPath, JSON.stringify(sessionInput, null, 2));
    console.log(`Wrote ${outPath}`);
}

main().catch(e => { console.error(e); process.exit(1); });
