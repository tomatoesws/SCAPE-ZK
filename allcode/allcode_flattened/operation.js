'use strict';

const { WorkloadModuleBase } = require('@hyperledger/caliper-core');

class ScapeOperationWorkload extends WorkloadModuleBase {
    async initializeWorkloadModule(workerIndex, totalWorkers, roundIndex, roundArguments, sutAdapter, sutContext) {
        await super.initializeWorkloadModule(workerIndex, totalWorkers, roundIndex, roundArguments, sutAdapter, sutContext);
        this.txIndex = 0;
        this.contractId = roundArguments.contractId || 'scapezk';
        this.operation = roundArguments.operation;
        this.prefix = roundArguments.prefix || this.operation.toLowerCase();
    }

    async submitTransaction() {
        this.txIndex++;
        const unique = `${this.prefix}-w${this.workerIndex}-r${this.roundIndex}-tx${this.txIndex}-${Date.now()}`;
        const request = this.createRequest(unique);
        await this.sutAdapter.sendRequests(request);
    }

    createRequest(unique) {
        switch (this.operation) {
        case 'Register':
            return this.createWriteRequest('Register', [
                unique,
                `cid-${unique}`,
                `hroot-${unique}`,
                `tag-${unique}`,
                `policy-${unique}`,
                `owner-${this.workerIndex}`
            ]);

        case 'VerifyProof':
            return this.createWriteRequest('VerifyProof', [
                `ctx-${unique}`,
                `bid-${unique}`,
                `sig-${unique}`
            ]);

        case 'Revoke':
            return this.createWriteRequest('Revoke', [`user-${unique}`]);

        case 'UpdateCred':
            return this.createWriteRequest('UpdateCred', [`user-${unique}`]);

        case 'RecordExists':
            return {
                contractId: this.contractId,
                contractFunction: 'RecordExists',
                contractArguments: [`record-${unique}`],
                invokerMspId: 'Org1MSP',
                invokerIdentity: 'Admin@org1.example.com',
                readOnly: true
            };

        default:
            throw new Error(`Unsupported SCAPE-ZK operation: ${this.operation}`);
        }
    }

    createWriteRequest(contractFunction, contractArguments) {
        return {
            contractId: this.contractId,
            contractFunction,
            contractArguments,
            invokerMspId: 'Org1MSP',
            invokerIdentity: 'Admin@org1.example.com',
            readOnly: false
        };
    }
}

function createWorkloadModule() {
    return new ScapeOperationWorkload();
}

module.exports.createWorkloadModule = createWorkloadModule;
