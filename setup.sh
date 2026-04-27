#!/bin/bash
set -e

echo "=========================================================="
echo "SCAPE-ZK Network Setup (4 Peers, 1 Orderer)"
echo "=========================================================="

if [ ! -d "fabric-samples" ]; then
  echo "Downloading Hyperledger Fabric v2.5.4 binaries..."
  curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh
  ./install-fabric.sh docker samples binary 2.5.4 1.5.7
fi

export PATH=${PWD}/fabric-samples/bin:$PATH
export FABRIC_CFG_PATH=${PWD}/fabric-samples/config/
export CONTAINER_CLI_COMPOSE="docker compose"

echo "=========================================================="
echo "Applying 4-peer configuration to test-network"
echo "=========================================================="

cd fabric-samples/test-network
./network.sh down

sed -i 's/COMPOSE_FILES="-f compose\/${COMPOSE_FILE_BASE} -f compose\/${CONTAINER_CLI}\/${CONTAINER_CLI}-${COMPOSE_FILE_BASE}"/COMPOSE_FILES="-f compose\/${COMPOSE_FILE_BASE} -f compose\/${CONTAINER_CLI}\/${CONTAINER_CLI}-${COMPOSE_FILE_BASE} -f compose\/docker-compose-peer1.yaml"/g' network.sh

echo "Bringing up the network (4 Peers, 1 Orderer) and creating channel 'scapechannel'..."

./network.sh up createChannel -c scapechannel

echo "=========================================================="
echo "Network started successfully!"
echo "Note: peer1.org1 and peer1.org2 containers are running."
echo "=========================================================="

echo "Next steps:"
echo "1. Install Go 1.23.6 on your machine."
echo "2. In chaincode-go/, run 'go mod tidy' and 'go build'."
echo "3. Run this command to deploy the chaincode:"
echo "   cd fabric-samples/test-network && ./network.sh deployCC -ccn scapezk -ccp ../../../chaincode-go -ccl go -c scapechannel"
echo "=========================================================="
