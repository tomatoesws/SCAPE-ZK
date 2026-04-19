#!/usr/bin/env bash
# SCAPE-ZK Attribute Sweep — Member A
# Compiles Session circuit at N in {5, 20, 50} using chunked Poseidon.

set -euo pipefail

ROOT=~/scape-zk
CIRCUITS="$ROOT/circuits"
KEYS="$ROOT/keys"
PTAU="$ROOT/ptau/powersOfTau28_hez_final_16.ptau"

cd "$ROOT"

for N in 5 20 50; do
    echo ""
    echo "================================================================"
    echo "SWEEPING N=$N attributes"
    echo "================================================================"

    # Create parameterized variant
    sed "s/SessionCPCP(10)/SessionCPCP($N)/g" "$CIRCUITS/session.circom" \
        > "$CIRCUITS/session_$N.circom"

    # Compile
    echo "[$N] Compiling..."
    cd "$CIRCUITS"
    circom "session_$N.circom" --r1cs --wasm --sym -l "$ROOT/node_modules"

    # Constraint info
    echo ""
    echo "[$N] Constraint info:"
    snarkjs r1cs info "session_$N.r1cs" | grep -E "Constraints|Wires|Private Inputs|Public Inputs"

    # Trusted setup
    echo "[$N] Trusted setup..."
    cd "$ROOT"
    snarkjs groth16 setup "$CIRCUITS/session_$N.r1cs" "$PTAU" "$KEYS/session_${N}_0000.zkey" 2>&1 | tail -3
    snarkjs zkey contribute "$KEYS/session_${N}_0000.zkey" "$KEYS/session_${N}_final.zkey" \
        --name="sweep N=$N" -e="$(head -c 32 /dev/urandom | base64)" 2>&1 | tail -3
    snarkjs zkey export verificationkey "$KEYS/session_${N}_final.zkey" "$KEYS/session_${N}_vkey.json" 2>&1 | tail -2
    echo "[$N] zkey size: $(du -h $KEYS/session_${N}_final.zkey | cut -f1)"

    echo "[$N] Done."
done

echo ""
echo "================================================================"
echo "Attribute sweep compile+setup complete."
echo "Next: generate inputs and benchmark each variant."
echo "================================================================"
