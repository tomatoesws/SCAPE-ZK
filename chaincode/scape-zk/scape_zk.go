package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing SCAPE-ZK state
type SmartContract struct {
	contractapi.Contract
}

// Record describes basic details of what makes up an anchored EHR metadata
type Record struct {
	ID           string `json:"id"`
	CID          string `json:"cid"`
	Hroot        string `json:"hroot"`
	Tag          string `json:"tag"`
	PolicyDigest string `json:"policyDigest"`
	Owner        string `json:"owner"`
	Timestamp    int64  `json:"timestamp"`
}

// AuthLog tracks authenticated requests and contexts
type AuthLog struct {
	ContextID string `json:"ctx"`
	Status    string `json:"status"` // "approved" or "rejected"
	BID       string `json:"bid"`
	Timestamp int64  `json:"timestamp"`
}

// Epoch represents the global or user-specific revocation state
type Epoch struct {
	Version int `json:"ver"`
}

// Batch represents an anchored batch of EHR metadata
type Batch struct {
	BID       string   `json:"bid"`
	Hroot     string   `json:"hroot"`
	Records   []string `json:"records"` // Array of record IDs
	Timestamp int64    `json:"timestamp"`
}

func txTimestampMillis(ctx contractapi.TransactionContextInterface) (int64, error) {
	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return 0, fmt.Errorf("failed to get transaction timestamp: %v", err)
	}
	return txTimestamp.Seconds*1000 + int64(txTimestamp.Nanos)/int64(time.Millisecond), nil
}

// InitLedger adds a base set of records to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	// Initialize global epoch at version 0
	epoch := Epoch{Version: 0}
	epochJSON, err := json.Marshal(epoch)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState("global_epoch", epochJSON)
	if err != nil {
		return fmt.Errorf("failed to put to world state. %v", err)
	}

	return nil
}

// Register anchors a new encrypted EHR's metadata on-chain
func (s *SmartContract) Register(ctx contractapi.TransactionContextInterface, id string, cid string, hroot string, tag string, policyDigest string, owner string) error {
	startTime := time.Now()

	timestamp, err := txTimestampMillis(ctx)
	if err != nil {
		return err
	}

	exists, err := s.RecordExists(ctx, id)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the record %s already exists", id)
	}

	record := Record{
		ID:           id,
		CID:          cid,
		Hroot:        hroot,
		Tag:          tag,
		PolicyDigest: policyDigest,
		Owner:        owner,
		Timestamp:    timestamp,
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(id, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to put to world state. %v", err)
	}

	// Logging latency for instrumentation
	elapsed := time.Since(startTime)
	fmt.Printf("Register execution time: %s\n", elapsed)

	return nil
}

// VerifyProof represents the O(1) verification of aggregated BLS signatures.
// Currently acts as a skeleton to mock verification and log the authentication event.
func (s *SmartContract) VerifyProof(ctx contractapi.TransactionContextInterface, ctxID string, bid string, aggSignature string) error {
	startTime := time.Now()

	timestamp, err := txTimestampMillis(ctx)
	if err != nil {
		return err
	}

	// In a real implementation, BLS pairing operations would be executed here.
	// For benchmarking, we can introduce a simulated delay or implement pairing ops later.
	// e(sigma_agg, g) == e(Q_agg, PK_Fog)

	// Mocking successful verification
	authLog := AuthLog{
		ContextID: ctxID,
		Status:    "approved",
		BID:       bid,
		Timestamp: timestamp,
	}

	authLogJSON, err := json.Marshal(authLog)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState("auth_"+ctxID, authLogJSON)
	if err != nil {
		return fmt.Errorf("failed to put to world state. %v", err)
	}

	// Logging latency for instrumentation
	elapsed := time.Since(startTime)
	fmt.Printf("VerifyProof execution time: %s\n", elapsed)

	return nil
}

// Revoke increments the user-specific epoch counter, enforcing context-bound forward secrecy
func (s *SmartContract) Revoke(ctx contractapi.TransactionContextInterface, userID string) error {
	startTime := time.Now()

	epochKey := "epoch_" + userID
	epochJSON, err := ctx.GetStub().GetState(epochKey)
	if err != nil {
		return fmt.Errorf("failed to read from world state: %v", err)
	}

	var epoch Epoch
	if epochJSON == nil {
		epoch = Epoch{Version: 1} // Initial revocation creates version 1
	} else {
		err = json.Unmarshal(epochJSON, &epoch)
		if err != nil {
			return err
		}
		epoch.Version++
	}

	newEpochJSON, err := json.Marshal(epoch)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(epochKey, newEpochJSON)
	if err != nil {
		return err
	}

	// Logging latency for instrumentation
	elapsed := time.Since(startTime)
	fmt.Printf("Revoke execution time: %s\n", elapsed)

	return nil
}

// CommitBatch anchors a batch of EHR metadata
func (s *SmartContract) CommitBatch(ctx contractapi.TransactionContextInterface, bid string, hroot string, recordsJSON string) error {
	startTime := time.Now()

	timestamp, err := txTimestampMillis(ctx)
	if err != nil {
		return err
	}

	var records []string
	err = json.Unmarshal([]byte(recordsJSON), &records)
	if err != nil {
		return fmt.Errorf("failed to unmarshal records array: %v", err)
	}

	batch := Batch{
		BID:       bid,
		Hroot:     hroot,
		Records:   records,
		Timestamp: timestamp,
	}

	batchBytes, err := json.Marshal(batch)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState("batch_"+bid, batchBytes)
	if err != nil {
		return fmt.Errorf("failed to put batch to world state. %v", err)
	}

	// Logging latency for instrumentation
	elapsed := time.Since(startTime)
	fmt.Printf("CommitBatch execution time: %s\n", elapsed)

	return nil
}

// UpdateCred represents the O(1) credential update when the global epoch changes.
// Currently acts as a skeleton to mock the update and log the event.
func (s *SmartContract) UpdateCred(ctx contractapi.TransactionContextInterface, userID string) error {
	startTime := time.Now()

	epochKey := "epoch_" + userID
	epochJSON, err := ctx.GetStub().GetState(epochKey)
	if err != nil {
		return fmt.Errorf("failed to read from world state: %v", err)
	}

	var epoch Epoch
	if epochJSON == nil {
		epoch = Epoch{Version: 0}
	} else {
		err = json.Unmarshal(epochJSON, &epoch)
		if err != nil {
			return err
		}
	}

	// In SCAPE-ZK, UpdateCred would involve updating the user's membership witness
	// or specific CP-ABE components to the latest global epoch.
	// For benchmarking, we simulate a state update.
	epoch.Version++

	newEpochJSON, err := json.Marshal(epoch)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(epochKey, newEpochJSON)
	if err != nil {
		return err
	}

	// Logging latency for instrumentation
	elapsed := time.Since(startTime)
	fmt.Printf("UpdateCred execution time: %s\n", elapsed)

	return nil
}

// RecordExists returns true when record with given ID exists in world state
func (s *SmartContract) RecordExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return recordJSON != nil, nil
}

// GetEpoch reads the current epoch for a user
func (s *SmartContract) GetEpoch(ctx contractapi.TransactionContextInterface, userID string) (*Epoch, error) {
	epochKey := "epoch_" + userID
	epochJSON, err := ctx.GetStub().GetState(epochKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if epochJSON == nil {
		return &Epoch{Version: 0}, nil
	}

	var epoch Epoch
	err = json.Unmarshal(epochJSON, &epoch)
	if err != nil {
		return nil, err
	}

	return &epoch, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating SCAPE-ZK chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting SCAPE-ZK chaincode: %v", err)
	}
}
