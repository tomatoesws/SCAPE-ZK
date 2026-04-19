pragma circom 2.1.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/eddsaposeidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

// Chunked VC hash: handles any NUM_ATTRS by chaining Poseidon hashes
// in chunks of CHUNK_SIZE attributes plus a running accumulator.
// Safe cryptographically: Poseidon is collision-resistant, and chaining
// preserves collision resistance (Merkle-Damgard-like composition).
template ChunkedHash(NUM_INPUTS, CHUNK_SIZE) {
    signal input in[NUM_INPUTS];
    signal output out;

    // Compute number of chunks (ceiling division)
    var NUM_CHUNKS = (NUM_INPUTS + CHUNK_SIZE - 1) \ CHUNK_SIZE;

    // If everything fits in one chunk, direct Poseidon
    if (NUM_CHUNKS == 1) {
        component h = Poseidon(NUM_INPUTS);
        for (var i = 0; i < NUM_INPUTS; i++) {
            h.inputs[i] <== in[i];
        }
        out <== h.out;
    } else {
        // Chunked: accumulator = Poseidon(prev_acc, chunk_items...)
        // Chunk 0: Poseidon of first CHUNK_SIZE elements
        component firstChunk = Poseidon(CHUNK_SIZE);
        for (var i = 0; i < CHUNK_SIZE; i++) {
            firstChunk.inputs[i] <== in[i];
        }
        signal acc[NUM_CHUNKS];
        acc[0] <== firstChunk.out;

        // Subsequent chunks: Poseidon(acc[k-1], chunk_k_items...)
        component chunks[NUM_CHUNKS - 1];
        for (var c = 1; c < NUM_CHUNKS; c++) {
            var start = c * CHUNK_SIZE;
            var end = start + CHUNK_SIZE;
            if (end > NUM_INPUTS) end = NUM_INPUTS;
            var chunk_len = end - start;
            // Poseidon(acc, item_1, ..., item_chunk_len) = chunk_len + 1 inputs
            chunks[c - 1] = Poseidon(chunk_len + 1);
            chunks[c - 1].inputs[0] <== acc[c - 1];
            for (var i = 0; i < chunk_len; i++) {
                chunks[c - 1].inputs[i + 1] <== in[start + i];
            }
            acc[c] <== chunks[c - 1].out;
        }
        out <== acc[NUM_CHUNKS - 1];
    }
}

template SessionCPCP(NUM_ATTRS) {
    signal input C_VC;
    signal input psi;
    signal input PK_Issuer_Ax;
    signal input PK_Issuer_Ay;
    signal input t_exp;
    signal input tau_now;

    signal input attributes[NUM_ATTRS];
    signal input DID_DU;
    signal input sig_R8x;
    signal input sig_R8y;
    signal input sig_S;
    signal input r;
    signal input expected_attrs[NUM_ATTRS];

    // Chunk size 14 leaves room for +2 (DID_DU and t_exp) within the 16-input limit
    var CHUNK = 14;

    // VC hash: combine DID_DU, attributes, t_exp using chunked hashing
    var VC_LEN = NUM_ATTRS + 2;
    component vcHash = ChunkedHash(VC_LEN, CHUNK);
    vcHash.in[0] <== DID_DU;
    for (var i = 0; i < NUM_ATTRS; i++) {
        vcHash.in[i + 1] <== attributes[i];
    }
    vcHash.in[NUM_ATTRS + 1] <== t_exp;

    // EdDSA
    component sigCheck = EdDSAPoseidonVerifier();
    sigCheck.enabled <== 1;
    sigCheck.Ax <== PK_Issuer_Ax;
    sigCheck.Ay <== PK_Issuer_Ay;
    sigCheck.R8x <== sig_R8x;
    sigCheck.R8y <== sig_R8y;
    sigCheck.S   <== sig_S;
    sigCheck.M   <== vcHash.out;

    // Policy match
    for (var j = 0; j < NUM_ATTRS; j++) {
        attributes[j] === expected_attrs[j];
    }
    // Policy hash: also chunked since it can hit the 16-input limit
    component policyHash = ChunkedHash(NUM_ATTRS, CHUNK);
    for (var k = 0; k < NUM_ATTRS; k++) {
        policyHash.in[k] <== expected_attrs[k];
    }
    policyHash.out === psi;

    // Commitment
    component com = Poseidon(2);
    com.inputs[0] <== vcHash.out;
    com.inputs[1] <== r;
    com.out === C_VC;

    // Expiration
    component exp = LessEqThan(64);
    exp.in[0] <== tau_now;
    exp.in[1] <== t_exp;
    exp.out === 1;
}

component main { public [C_VC, psi, PK_Issuer_Ax, PK_Issuer_Ay, t_exp, tau_now] } = SessionCPCP(5);
