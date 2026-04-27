#!/bin/bash
set -e

# Configuration
TEST_NET_PATH="network/fabric-samples/test-network"
TLS_CA_DIR="network/shared-tls-ca"
mkdir -p $TLS_CA_DIR

echo "Generating Shared TLS Root CA..."
openssl ecparam -name prime256v1 -genkey -noout -out $TLS_CA_DIR/tls-ca.key
openssl req -new -x509 -sha256 -key $TLS_CA_DIR/tls-ca.key -out $TLS_CA_DIR/tls-ca.crt -days 3650 -subj "/C=US/ST=California/L=San Francisco/O=SCAPE-ZK/CN=shared-tls-ca"

generate_node_cert() {
    local node_name=$1
    local node_dir=$2
    local alt_names=$3

    echo "Generating TLS cert for $node_name..."
    mkdir -p $node_dir/tls
    
    openssl ecparam -name prime256v1 -genkey -noout -out $node_dir/tls/server.key
    openssl req -new -sha256 -key $node_dir/tls/server.key -out $node_dir/tls/server.csr -subj "/C=US/ST=California/L=San Francisco/O=SCAPE-ZK/CN=$node_name"
    
    # Create extension file for SANs
    cat > $node_dir/tls/ext.cnf <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = $alt_names
EOF

    openssl x509 -req -in $node_dir/tls/server.csr -CA $TLS_CA_DIR/tls-ca.crt -CAkey $TLS_CA_DIR/tls-ca.key -CAcreateserial \
        -out $node_dir/tls/server.crt -days 365 -sha256 -extfile $node_dir/tls/ext.cnf
    
    cp $TLS_CA_DIR/tls-ca.crt $node_dir/tls/ca.crt
    # Also update the MSP tlscacerts
    mkdir -p $node_dir/msp/tlscacerts
    cp $TLS_CA_DIR/tls-ca.crt $node_dir/msp/tlscacerts/ca.crt
    
    rm $node_dir/tls/server.csr $node_dir/tls/ext.cnf
}

# 1. Run cryptogen first to get the structure and Identity CAs
echo "Running cryptogen..."
cd $TEST_NET_PATH
./../bin/cryptogen generate --config=./organizations/cryptogen/crypto-config-org1.yaml --output=organizations
./../bin/cryptogen generate --config=./organizations/cryptogen/crypto-config-org2.yaml --output=organizations
./../bin/cryptogen generate --config=./organizations/cryptogen/crypto-config-orderer.yaml --output=organizations
cd ../../../

# 2. Overwrite TLS certs with Shared CA
ORGS_DIR="$TEST_NET_PATH/organizations"

# Org1 Peers
generate_node_cert "peer0.org1.example.com" "$ORGS_DIR/peerOrganizations/org1.example.com/peers/peer0.org1.example.com" "DNS:peer0.org1.example.com,DNS:localhost,IP:127.0.0.1"
generate_node_cert "peer1.org1.example.com" "$ORGS_DIR/peerOrganizations/org1.example.com/peers/peer1.org1.example.com" "DNS:peer1.org1.example.com,DNS:localhost,IP:127.0.0.1"

# Org2 Peers
generate_node_cert "peer0.org2.example.com" "$ORGS_DIR/peerOrganizations/org2.example.com/peers/peer0.org2.example.com" "DNS:peer0.org2.example.com,DNS:localhost,IP:127.0.0.1"
generate_node_cert "peer1.org2.example.com" "$ORGS_DIR/peerOrganizations/org2.example.com/peers/peer1.org2.example.com" "DNS:peer1.org2.example.com,DNS:localhost,IP:127.0.0.1"

# Orderer
generate_node_cert "orderer.example.com" "$ORGS_DIR/ordererOrganizations/example.com/orderers/orderer.example.com" "DNS:orderer.example.com,DNS:localhost,IP:127.0.0.1"

# Also update the org-level MSP tlscacerts so client tools trust the nodes
cp $TLS_CA_DIR/tls-ca.crt $ORGS_DIR/peerOrganizations/org1.example.com/msp/tlscacerts/ca.crt
cp $TLS_CA_DIR/tls-ca.crt $ORGS_DIR/peerOrganizations/org2.example.com/msp/tlscacerts/ca.crt
cp $TLS_CA_DIR/tls-ca.crt $ORGS_DIR/ordererOrganizations/example.com/msp/tlscacerts/ca.crt

echo "Shared TLS CA and certificates generated successfully."
