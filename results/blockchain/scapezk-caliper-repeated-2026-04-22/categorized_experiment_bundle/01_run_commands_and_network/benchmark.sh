#!/bin/bash

# Configuration
CHANNEL="scapechannel"
CC_NAME="scapezk"
ORG1_PEER="localhost:7051"
ORG2_PEER="localhost:9051"
ITERATIONS=10

# Absolute paths
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
export FABRIC_CFG_PATH="${SCRIPT_DIR}/../config"
PEER_BIN="${SCRIPT_DIR}/../bin/peer"
ORDERER_CA="${SCRIPT_DIR}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
ORG1_CA="${SCRIPT_DIR}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem"
ORG2_CA="${SCRIPT_DIR}/organizations/peerOrganizations/org2.example.com/tlsca/tlsca.org2.example.com-cert.pem"
ORG1_MSP="${SCRIPT_DIR}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
ORG2_MSP="${SCRIPT_DIR}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp"

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$ORG1_CA"
export CORE_PEER_MSPCONFIGPATH="$ORG1_MSP"
export CORE_PEER_ADDRESS="localhost:7051"

echo "=========================================================="
echo "SCAPE-ZK Performance Benchmarking (10 Iterations)"
echo "=========================================================="

echo -n "Measuring Register: "
TOTAL=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%N)
    $PEER_BIN chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C $CHANNEL -n $CC_NAME --peerAddresses $ORG1_PEER --tlsRootCertFiles "$ORG1_CA" --peerAddresses $ORG2_PEER --tlsRootCertFiles "$ORG2_CA" -c "{\"function\":\"Register\",\"Args\":[\"r$i\", \"c\", \"h\", \"t\", \"p\", \"o\"]}" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    TOTAL=$((TOTAL + LATENCY))
    echo -n "."
    sleep 1
done
echo " DONE (Mean: $((TOTAL / ITERATIONS))ms)"

echo -n "Measuring VerifyProof: "
TOTAL=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%N)
    $PEER_BIN chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C $CHANNEL -n $CC_NAME --peerAddresses $ORG1_PEER --tlsRootCertFiles "$ORG1_CA" --peerAddresses $ORG2_PEER --tlsRootCertFiles "$ORG2_CA" -c "{\"function\":\"VerifyProof\",\"Args\":[\"ctx$i\", \"b\", \"s\"]}" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    TOTAL=$((TOTAL + LATENCY))
    echo -n "."
    sleep 1
done
echo " DONE (Mean: $((TOTAL / ITERATIONS))ms)"

echo -n "Measuring Revoke: "
TOTAL=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%N)
    $PEER_BIN chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C $CHANNEL -n $CC_NAME --peerAddresses $ORG1_PEER --tlsRootCertFiles "$ORG1_CA" --peerAddresses $ORG2_PEER --tlsRootCertFiles "$ORG2_CA" -c "{\"function\":\"Revoke\",\"Args\":[\"u$i\"]}" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    TOTAL=$((TOTAL + LATENCY))
    echo -n "."
    sleep 1
done
echo " DONE (Mean: $((TOTAL / ITERATIONS))ms)"

echo -n "Measuring UpdateCred: "
TOTAL=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%N)
    $PEER_BIN chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C $CHANNEL -n $CC_NAME --peerAddresses $ORG1_PEER --tlsRootCertFiles "$ORG1_CA" --peerAddresses $ORG2_PEER --tlsRootCertFiles "$ORG2_CA" -c "{\"function\":\"UpdateCred\",\"Args\":[\"u$i\"]}" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    TOTAL=$((TOTAL + LATENCY))
    echo -n "."
    sleep 1
done
echo " DONE (Mean: $((TOTAL / ITERATIONS))ms)"

# Switch to Org2 for Query
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE="$ORG2_CA"
export CORE_PEER_MSPCONFIGPATH="$ORG2_MSP"
export CORE_PEER_ADDRESS="localhost:9051"

echo -n "Measuring Cross-Domain Query: "
TOTAL=0
for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%N)
    $PEER_BIN chaincode query -C $CHANNEL -n $CC_NAME -c "{\"function\":\"RecordExists\",\"Args\":[\"r$i\"]}" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    TOTAL=$((TOTAL + LATENCY))
    echo -n "."
    sleep 1
done
echo " DONE (Mean: $((TOTAL / ITERATIONS))ms)"

echo "=========================================================="
echo "Benchmarks Completed."
