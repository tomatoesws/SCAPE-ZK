pragma circom 2.1.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/eddsaposeidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

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

    component vcHash = Poseidon(NUM_ATTRS + 2);
    vcHash.inputs[0] <== DID_DU;
    for (var i = 0; i < NUM_ATTRS; i++) {
        vcHash.inputs[i + 1] <== attributes[i];
    }
    vcHash.inputs[NUM_ATTRS + 1] <== t_exp;

    component sigCheck = EdDSAPoseidonVerifier();
    sigCheck.enabled <== 1;
    sigCheck.Ax <== PK_Issuer_Ax;
    sigCheck.Ay <== PK_Issuer_Ay;
    sigCheck.R8x <== sig_R8x;
    sigCheck.R8y <== sig_R8y;
    sigCheck.S   <== sig_S;
    sigCheck.M   <== vcHash.out;

    for (var j = 0; j < NUM_ATTRS; j++) {
        attributes[j] === expected_attrs[j];
    }
    component policyHash = Poseidon(NUM_ATTRS);
    for (var k = 0; k < NUM_ATTRS; k++) {
        policyHash.inputs[k] <== expected_attrs[k];
    }
    policyHash.out === psi;

    component com = Poseidon(2);
    com.inputs[0] <== vcHash.out;
    com.inputs[1] <== r;
    com.out === C_VC;

    component exp = LessEqThan(64);
    exp.in[0] <== tau_now;
    exp.in[1] <== t_exp;
    exp.out === 1;
}

component main { public [C_VC, psi, PK_Issuer_Ax, PK_Issuer_Ay, t_exp, tau_now] } = SessionCPCP(10);
