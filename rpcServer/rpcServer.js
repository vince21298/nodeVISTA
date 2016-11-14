#!/usr/bin/env node
'use strict';

var net = require('net');
var fs = require('fs');
var util = require('util');
var _ = require('underscore');
var LOGGER = require('./logger.js');

var mvdmClient = require('./mvdmClient');
var mvdmManagement = require('./mvdmManagement');
var EventManager = require('./eventManager');

// import for multiprocess management
var qoper8 = require('ewd-qoper8');
var processQueue = new qoper8.masterProcess();

var server;

var NUL = '\u0000';
var SOH = '\u0001';
var EOT = '\u0004';
var ENQ = '\u0005';


console.log("__dirname: %j, __filename: %j", __dirname, __filename);
// check if config file is in current (operating) directory.
try {
    fs.accessSync(__dirname + '/config.js', fs.F_OK);
    console.log('using existing config.js');

} catch (e) {
    console.log('config.js does not exist, copying default. Please configure config.js');

    var conf = fs.readFileSync(__dirname + '/cfg/config.js');
    fs.writeFileSync(__dirname + '/config.js', conf);

    process.exit();


}

var CONFIG = require(__dirname + '/config.js');
var fromName = CONFIG.client.defaultName;
var capturePath = CONFIG.FILE.defaultCaptureFile;
var port = CONFIG.rpcServer.port;

processQueue.on('started', function() {
    this.worker.module = __dirname + '/rpcQWorker';
});

processQueue.on('start', function() {
    this.setWorkerPoolSize(CONFIG.workerQ.size);

});


processQueue.start();

var captureFile = fs.createWriteStream(capturePath, CONFIG.FILE.options);
// wait until the captureFile is open before continuing
captureFile.on("open", function (fd) {
    LOGGER.info("Capture file %s opened for writing", capturePath);
    captureFile.write("[\n");

    // Start up the server
    server = net.createServer();
    server.on('connection', handleConnection);
    server.listen(port, function () {
        LOGGER.info('RPCServer listening to %j', server.address());

        //start up mvdm client
        mvdmClient.init();
    });
});

// main function to handle the connection from the client
function handleConnection(conn) {
    var remoteAddress = conn.remoteAddress + ':' + conn.remotePort;
    LOGGER.info('New client connection from %s', remoteAddress);
    var chunk = '';

    conn.on('data', onConnectedData);
    conn.on('close', onConnectedClose);
    conn.on('error', onConnectedError);

    // handle data coming from the client
    function onConnectedData(data) {
        chunk += data;
        // find the end of a RPC packet
        var eotIndex = chunk.indexOf(EOT);

        // loop for each packet in the data chunk
        while (eotIndex > -1) {
            var response = '';

            // get a packet from the chunk (without the EOT)
            var rpcPacket = chunk.substr(0, eotIndex + 1);
            // remove the RPC packet from the chunk
            chunk = chunk.substring(eotIndex + 1)
            // find the end of the next RPC packet
            eotIndex = chunk.indexOf(EOT);

            // process the packet
            LOGGER.info('RECEIVED RPC from %s: %s', remoteAddress, data);


            //response = callRPC(rpcObject, rpcPacket);
            //
            //// write the response back to the client
            //LOGGER.info("SENDING RESPONSE to client: " + response);
            //var responseBuffer = new Buffer(response, 'binary');
            //
            //conn.write(responseBuffer);

            var messageObject = {};
            messageObject.method = 'callRPC';
            messageObject.ipAddress = conn.remoteAddress;
            messageObject.rpcPacket = rpcPacket;
            messageObject.isMvdmLocked = mvdmManagement.isMvdmLocked;
            messageObject.contextId = remoteAddress;
            processQueue.handleMessage(messageObject, function(responseObject) {
                LOGGER.debug("in rpcServer handleMessage from rpc responseObject = %j", responseObject);

                if (!responseObject.finished) {
                    // send() from worker handler
                    if (responseObject.type === 'emitRpcEvent') {
                        EventManager.emit('rpcCall', responseObject.message.event);
                    } else if (responseObject.type === 'emitMvdmEvent') {
                        EventManager.emit(responseObject.message.eventType, responseObject.message.event);
                    }
                } else {
                    // finished() from worker handler
                    if (responseObject.message.type === 'rpcResponse') {
                        // write out the rpc to a capture log
                        captureFile.write(JSON.stringify(responseObject.message.rpcObject, null, 2) + ",\n");

                        // write the response back to the client
                        LOGGER.info("SENDING RESPONSE to client: %j", responseObject.message.response);
                        var responseBuffer = new Buffer(responseObject.message.response, 'binary');

                        conn.write(responseBuffer);
                    }
                }
            });

        }
    }


    function onConnectedClose() {

        var messageObject = {};
        messageObject.method = 'dbReinit';
        processQueue.handleMessage(messageObject, function(responseObject) {
            LOGGER.debug("in rpcServer onConnectedClose after reinit");

        });


        //loggedIn = false;
        //USER = null;
        //FACILITY = null;
        LOGGER.info('CONNECTION from %s CLOSED', remoteAddress);
        conn.removeAllListeners();
        conn.end();
        conn.destroy();
    }

    function onConnectedError(err) {
        //loggedIn = false;
        //USER = null;
        //FACILITY = null;
        LOGGER.error('CONNECTION %s ERROR: %s', remoteAddress, err.message);
        conn.removeAllListeners();
        conn.end();
        conn.destroy();
    }


}

function copyFile(source, target, cb) {
    console.log('copying config.js source: %j, target: %j', source, target);

    var cbCalled = false;

    var rd = fs.createReadStream(source);
    rd.on("error", function(err) {
        console.log("read file error");
        done(err);
    });
    var wr = fs.createWriteStream(target);
    wr.on("error", function(err) {
        console.log("read file error");
        done(err);
    });
    wr.on("close", function(ex) {
        console.log("close");
        done();
    });
    console.log("BEFORE PIPE rd: %j, wr: %j", rd, wr);
    rd.pipe(wr);

    function done(err) {
        console.log("done? error: %j", err);
        if (!cbCalled) {
            cb(err);
            cbCalled = true;
        }
    }
}
