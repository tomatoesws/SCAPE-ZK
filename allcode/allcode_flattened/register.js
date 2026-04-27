'use strict';

const { WorkloadModuleBase } = require('@hyperledger/caliper-core');

class RegisterWorkload extends WorkloadModuleBase {
    async initializeWorkloadModule(workerIndex, totalWorkers, roundIndex, roundArguments, sutAdapter, sutContext) {
        await super.initializeWorkloadModule(workerIndex, totalWorkers, roundIndex, roundArguments, sutAdapter, sutContext);
        this.txIndex = 0;
        this.contractId = roundArguments.contractId || 'scapezk';
        this.prefix = roundArguments.prefix || 'caliper';
    }

    async submitTransaction() {
        this.txIndex++;
        const unique = `${this.prefix}-w${this.workerIndex}-r${this.roundIndex}-tx${this.txIndex}-${Date.now()}`;
        const request = {
            contractId: this.contractId,
            contractFunction: 'Register',
            contractArguments: [
                unique,
                `cid-${unique}`,
                `hroot-${unique}`,
                `tag-${unique}`,
                `policy-${unique}`,
                `owner-${this.workerIndex}`
            ],
            invokerMspId: 'Org1MSP',
            invokerIdentity: 'Admin@org1.example.com',
            readOnly: false
        };

        await this.sutAdapter.sendRequests(request);
    }
}

function createWorkloadModule() {
    return new RegisterWorkload();
}

module.exports.createWorkloadModule = createWorkloadModule;
