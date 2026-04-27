const { buildPoseidon, buildEddsa, buildBabyjub } = require("circomlibjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const NUM_ATTRS = 10;

async function main() {
    const poseidon = await buildPoseidon();
    const eddsa = await buildEddsa();
    const babyjub = await buildBabyjub();
    const F = poseidon.F;


    const toStr = (x) => F.toObject(x).toString();
    const toStrRaw = (x) => x.toString();




    const issuerPrv = Buffer.from("0001020304050607080900010203040506070809000102030405060708090001", "hex");
    const issuerPubPoint = eddsa.prv2pub(issuerPrv);
    const PK_Issuer_Ax = toStr(issuerPubPoint[0]);
    const PK_Issuer_Ay = toStr(issuerPubPoint[1]);


    const DID_DU = 12345678901234567890n;
    const attributes = [];
    for (let i = 0; i < NUM_ATTRS; i++) {
        attributes.push(BigInt(100 + i));
    }
    const t_exp = 2000000000n;
    const tau_now = 1700000000n;



    const vcInputs = [DID_DU, ...attributes, t_exp].map((x) => F.e(x));
    const vcHash = poseidon(vcInputs);



    const signature = eddsa.signPoseidon(issuerPrv, vcHash);
    const sig_R8x = toStr(signature.R8[0]);
    const sig_R8y = toStr(signature.R8[1]);
    const sig_S = signature.S.toString();


    const r = 987654321n;
    const C_VC = poseidon([vcHash, F.e(r)]);



    const expected_attrs = [...attributes];
    const psi = poseidon(expected_attrs.map((x) => F.e(x)));


    const sessionInput = {

        C_VC: toStrRaw(F.toObject(C_VC)),
        psi: toStrRaw(F.toObject(psi)),
        PK_Issuer_Ax,
        PK_Issuer_Ay,
        t_exp: t_exp.toString(),
        tau_now: tau_now.toString(),

        attributes: attributes.map((x) => x.toString()),
        DID_DU: DID_DU.toString(),
        sig_R8x,
        sig_R8y,
        sig_S,
        r: r.toString(),
        expected_attrs: expected_attrs.map((x) => x.toString()),
    };

    fs.writeFileSync(
        path.join(ROOT, "circuits", "input_session.json"),
        JSON.stringify(sessionInput, null, 2)
    );
    console.log("Wrote input_session.json");



    const ver = 1n;
    const tok = poseidon([
        F.e(DID_DU),
        C_VC,
        psi,
        F.e(ver),
        F.e(t_exp),
    ]);


    const ctx_i = poseidon([F.e(111n), F.e(222n), F.e(333n)]);
    const nonce_i = 42n;


    const mu_i = poseidon([tok, ctx_i, F.e(nonce_i)]);

    const requestInput = {

        mu_i: toStrRaw(F.toObject(mu_i)),
        ver: ver.toString(),

        tok: toStrRaw(F.toObject(tok)),
        DID_DU: DID_DU.toString(),
        C_VC: toStrRaw(F.toObject(C_VC)),
        psi: toStrRaw(F.toObject(psi)),
        t_exp: t_exp.toString(),
        ctx_i: toStrRaw(F.toObject(ctx_i)),
        nonce_i: nonce_i.toString(),
    };

    fs.writeFileSync(
        path.join(ROOT, "circuits", "input_request.json"),
        JSON.stringify(requestInput, null, 2)
    );
    console.log("Wrote input_request.json");

    console.log("\nBoth inputs are cryptographically consistent.");
    console.log("Session: valid EdDSA sig, valid commitment, policy matches.");
    console.log("Request: tok and mu_i derived from the same session state.");
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
