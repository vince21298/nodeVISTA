#!/usr/bin/env node

'use strict';

/**
 * Non-clinical models supported by the RPC Server: VDM, MVDM, rpcL
 */

// VDM Models
const vdmModel = [].concat(
    // patient
    require('mvdm/patient/vdmPatientModel').vdmModel);

// ClinicalRPCLocker models
const rpcLModel = [];

module.exports = {
    vdmModel,
    rpcLModel,
};