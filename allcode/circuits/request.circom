pragma circom 2.1.0;

include "../node_modules/circomlib/circuits/poseidon.circom";

template RequestCPCP() {
    signal input mu_i;
    signal input ver;

    signal input tok;
    signal input DID_DU;
    signal input C_VC;
    signal input psi;
    signal input t_exp;
    signal input ctx_i;
    signal input nonce_i;

    component tokHash = Poseidon(5);
    tokHash.inputs[0] <== DID_DU;
    tokHash.inputs[1] <== C_VC;
    tokHash.inputs[2] <== psi;
    tokHash.inputs[3] <== ver;
    tokHash.inputs[4] <== t_exp;
    tokHash.out === tok;

    component muHash = Poseidon(3);
    muHash.inputs[0] <== tok;
    muHash.inputs[1] <== ctx_i;
    muHash.inputs[2] <== nonce_i;
    muHash.out === mu_i;
}

component main { public [mu_i, ver] } = RequestCPCP();
