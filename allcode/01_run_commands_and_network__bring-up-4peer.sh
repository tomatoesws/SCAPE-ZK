#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BIN_DIR="$SCRIPT_DIR/../bin"
CHANNEL_NAME="scapechannel"

export PATH="$BIN_DIR:$PATH"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
fatal()   { echo -e "${RED}[FATAL]${NC} $*"; exit 1; }

info "Stopping and removing existing containers..."
docker compose \
  -f compose/compose-test-net.yaml \
  -f compose/docker-compose-peer1.yaml \
  down --volumes --remove-orphans 2>/dev/null || true

docker rm -f $(docker ps -aq --filter "label=service=hyperledger-fabric") 2>/dev/null || true
docker volume rm $(docker volume ls -q | grep -E "compose_|peer[01]\.(org[12]|orderer)") 2>/dev/null || true

info "Removing old crypto material..."
rm -rf organizations/peerOrganizations organizations/ordererOrganizations
mkdir -p channel-artifacts

info "Generating crypto for Org1 (peer0 + peer1)..."
cryptogen generate \
  --config=./organizations/cryptogen/crypto-config-org1.yaml \
  --output=organizations

info "Generating crypto for Org2 (peer0 + peer1)..."
cryptogen generate \
  --config=./organizations/cryptogen/crypto-config-org2.yaml \
  --output=organizations

info "Generating crypto for Orderer..."
cryptogen generate \
  --config=./organizations/cryptogen/crypto-config-orderer.yaml \
  --output=organizations

for peer in peer1.org1.example.com peer1.org2.example.com; do
  if [ ! -d "organizations/peerOrganizations/${peer#*.}/peers/$peer/tls" ]; then
    fatal "TLS certs missing for $peer — cryptogen failed"
  fi
done
info "All 4 peer TLS certificates generated."

info "Generating genesis block for channel '$CHANNEL_NAME'..."
export FABRIC_CFG_PATH="$SCRIPT_DIR/configtx"
configtxgen \
  -profile ChannelUsingRaft \
  -outputBlock ./channel-artifacts/${CHANNEL_NAME}.block \
  -channelID $CHANNEL_NAME

info "Starting orderer + 4 peers..."
export FABRIC_CFG_PATH="$SCRIPT_DIR/../config"

docker compose \
  -f compose/compose-test-net.yaml \
  -f compose/docker-compose-peer1.yaml \
  up -d

info "Waiting 5s for containers to stabilise..."
sleep 5

EXPECTED=("orderer.example.com" "peer0.org1.example.com" "peer1.org1.example.com" "peer0.org2.example.com" "peer1.org2.example.com")
for c in "${EXPECTED[@]}"; do
  STATUS=$(docker inspect --format='{{.State.Status}}' "$c" 2>/dev/null || echo "missing")
  if [ "$STATUS" != "running" ]; then
    docker logs "$c" 2>&1 | tail -20
    fatal "Container $c is $STATUS — check logs above"
  fi
  info "  ✓ $c is running"
done

info "Joining orderer to channel '$CHANNEL_NAME'..."

ORDERER_ADMIN_TLS_CA="$SCRIPT_DIR/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
ORDERER_ADMIN_TLS_SIGN_CERT="$SCRIPT_DIR/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt"
ORDERER_ADMIN_TLS_SIGN_KEY="$SCRIPT_DIR/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.key"

osnadmin channel join \
  --channelID $CHANNEL_NAME \
  --config-block ./channel-artifacts/${CHANNEL_NAME}.block \
  -o localhost:7053 \
  --ca-file "$ORDERER_ADMIN_TLS_CA" \
  --client-cert "$ORDERER_ADMIN_TLS_SIGN_CERT" \
  --client-key "$ORDERER_ADMIN_TLS_SIGN_KEY"

info "Waiting 3s for orderer to process genesis block..."
sleep 3

export CORE_PEER_TLS_ENABLED=true
export FABRIC_CFG_PATH="$SCRIPT_DIR/../config"
BLOCKFILE="./channel-artifacts/${CHANNEL_NAME}.block"

ORG1_TLSCA="$SCRIPT_DIR/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem"
ORG2_TLSCA="$SCRIPT_DIR/organizations/peerOrganizations/org2.example.com/tlsca/tlsca.org2.example.com-cert.pem"
ORG1_ADMIN_MSP="$SCRIPT_DIR/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
ORG2_ADMIN_MSP="$SCRIPT_DIR/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp"
ORDERER_TLS_CA="$SCRIPT_DIR/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"

join_peer() {
  local LABEL="$1"
  local MSPID="$2"
  local ADDR="$3"
  local TLS_CA="$4"
  local ADMIN_MSP="$5"

  info "Joining $LABEL to $CHANNEL_NAME..."
  export CORE_PEER_LOCALMSPID="$MSPID"
  export CORE_PEER_TLS_ROOTCERT_FILE="$TLS_CA"
  export CORE_PEER_MSPCONFIGPATH="$ADMIN_MSP"
  export CORE_PEER_ADDRESS="$ADDR"

  local RETRY=0
  until peer channel join -b "$BLOCKFILE" 2>&1; do
    RETRY=$((RETRY+1))
    if [ $RETRY -ge 5 ]; then fatal "$LABEL failed to join after 5 attempts"; fi
    warn "  Retry $RETRY/5 for $LABEL..."
    sleep 3
  done
  info "  ✓ $LABEL joined $CHANNEL_NAME"
}

join_peer "peer0.org1" Org1MSP localhost:7051  "$ORG1_TLSCA" "$ORG1_ADMIN_MSP"
join_peer "peer1.org1" Org1MSP localhost:8051  "$ORG1_TLSCA" "$ORG1_ADMIN_MSP"
join_peer "peer0.org2" Org2MSP localhost:9051  "$ORG2_TLSCA" "$ORG2_ADMIN_MSP"
join_peer "peer1.org2" Org2MSP localhost:10051 "$ORG2_TLSCA" "$ORG2_ADMIN_MSP"

info "Setting anchor peers..."

export OVERRIDE_ORG=""
set +u
. scripts/setAnchorPeer.sh 1 $CHANNEL_NAME
. scripts/setAnchorPeer.sh 2 $CHANNEL_NAME
set -u

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  4-peer network is UP on '$CHANNEL_NAME'${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  peer0.org1 → localhost:7051"
echo "  peer1.org1 → localhost:8051"
echo "  peer0.org2 → localhost:9051"
echo "  peer1.org2 → localhost:10051"
echo "  orderer    → localhost:7050"
echo ""
echo "Next step: install + commit scapezk chaincode"
echo "  ./scripts/deployCC.sh $CHANNEL_NAME ../../../chaincode-go golang 1.0"
