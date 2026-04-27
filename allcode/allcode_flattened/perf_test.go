package main

import (
	"fmt"
	"testing"
	"time"

	"github.com/golang/protobuf/ptypes/timestamp"
	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/stretchr/testify/mock"
)

type SimpleMockStub struct {
	shim.ChaincodeStubInterface
	mock.Mock
	state map[string][]byte
}

func (m *SimpleMockStub) PutState(key string, value []byte) error {
	m.state[key] = value
	return nil
}

func (m *SimpleMockStub) GetState(key string) ([]byte, error) {
	return m.state[key], nil
}

func (m *SimpleMockStub) GetTxTimestamp() (*timestamp.Timestamp, error) {
	return &timestamp.Timestamp{Seconds: 1776745800, Nanos: 123000000}, nil
}

type SimpleMockContext struct {
	contractapi.TransactionContext
	stub *SimpleMockStub
}

func (m *SimpleMockContext) GetStub() shim.ChaincodeStubInterface {
	return m.stub
}

func BenchmarkRegister(b *testing.B) {
	contract := new(SmartContract)
	stub := &SimpleMockStub{state: make(map[string][]byte)}
	ctx := &SimpleMockContext{stub: stub}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		id := fmt.Sprintf("ID-%d", i)
		_ = contract.Register(ctx, id, "CID", "ROOT", "TAG", "POLICY", "OWNER")
	}
}

func BenchmarkVerifyProof(b *testing.B) {
	contract := new(SmartContract)
	stub := &SimpleMockStub{state: make(map[string][]byte)}
	ctx := &SimpleMockContext{stub: stub}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ctxID := fmt.Sprintf("CTX-%d", i)
		_ = contract.VerifyProof(ctx, ctxID, "BID", "AGG_SIG")
	}
}

func TestPerformanceMetrics(t *testing.T) {

	fmt.Println("Starting performance metrics test...")
	start := time.Now()

	contract := new(SmartContract)
	stub := &SimpleMockStub{state: make(map[string][]byte)}
	ctx := &SimpleMockContext{stub: stub}

	err := contract.Register(ctx, "T1", "C1", "R1", "T1", "P1", "O1")
	if err != nil {
		t.Fatalf("Register failed: %v", err)
	}

	fmt.Printf("Single Register Latency: %s\n", time.Since(start))
}
