package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type SmartContract struct {
	contractapi.Contract
}

type Record struct {
	ID           string `json:"id"`
	CID          string `json:"cid"`
	Hroot        string `json:"hroot"`
	Tag          string `json:"tag"`
	PolicyDigest string `json:"policyDigest"`
	Owner        string `json:"owner"`
	Timestamp    int64  `json:"timestamp"`
}

type AuthLog struct {
	ContextID string `json:"ctx"`
	Status    string `json:"status"`
	BID       string `json:"bid"`
	Timestamp int64  `json:"timestamp"`
}

type Epoch struct {
	Version int `json:"ver"`
}

type Batch struct {
	BID       string   `json:"bid"`
	Hroot     string   `json:"hroot"`
	Records   []string `json:"records"`
	Timestamp int64    `json:"timestamp"`
}

func txTimestampMillis(ctx contractapi.TransactionContextInterface) (int64, error) {
	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return 0, fmt.Errorf("failed to get transaction timestamp: %v", err)
	}
	return txTimestamp.Seconds*1000 + int64(txTimestamp.Nanos)/int64(time.Millisecond), nil
}

func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {

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


	elapsed := time.Since(startTime)
	fmt.Printf("Register execution time: %s\n", elapsed)

	return nil
}

func (s *SmartContract) VerifyProof(ctx contractapi.TransactionContextInterface, ctxID string, bid string, aggSignature string) error {
	startTime := time.Now()

	timestamp, err := txTimestampMillis(ctx)
	if err != nil {
		return err
	}






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


	elapsed := time.Since(startTime)
	fmt.Printf("VerifyProof execution time: %s\n", elapsed)

	return nil
}

func (s *SmartContract) Revoke(ctx contractapi.TransactionContextInterface, userID string) error {
	startTime := time.Now()

	epochKey := "epoch_" + userID
	epochJSON, err := ctx.GetStub().GetState(epochKey)
	if err != nil {
		return fmt.Errorf("failed to read from world state: %v", err)
	}

	var epoch Epoch
	if epochJSON == nil {
		epoch = Epoch{Version: 1}
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


	elapsed := time.Since(startTime)
	fmt.Printf("Revoke execution time: %s\n", elapsed)

	return nil
}

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


	elapsed := time.Since(startTime)
	fmt.Printf("CommitBatch execution time: %s\n", elapsed)

	return nil
}

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




	epoch.Version++

	newEpochJSON, err := json.Marshal(epoch)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(epochKey, newEpochJSON)
	if err != nil {
		return err
	}


	elapsed := time.Since(startTime)
	fmt.Printf("UpdateCred execution time: %s\n", elapsed)

	return nil
}

func (s *SmartContract) RecordExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(id)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return recordJSON != nil, nil
}

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
