// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import * as mqtt from 'mqtt';
import { IClientOptions } from 'mqtt';
import {MqttEdgeAuth} from '../helpers';

// SAMPLE 1
//
// Demonstrates how to connect to IoT Edge as a module and disconnect again.

function handleOnConnect(client: mqtt.Client) {
  return function (rc: mqtt.Packet) {
    console.log(`handleOnConnect called with rc=${rc} (${rc.cmd})`);
    client.end();
  }
}

function main() {
  console.log('Azure IoT Edge Protocol Translation Module (PTM) Sample');
  const auth = MqttEdgeAuth.createFromEnvironment();
  // In this sample, we use the TLS context that the auth object builds for
  // us.  We could also build our own from the contents of the auth object
  let options: IClientOptions = auth;
  options.protocol = 'mqtts';
  // wait for the connection, but don't wait too long
  options.connectTimeout = 30 * 1000;
  console.log("Connecting");
  // Create an MQTT client object, passing in the credentials we
  // get from the auth object
  const client  = mqtt.connect(auth);
  // Connect. When this returns, we're not actually connected yet.
  // We have to wait for `handleOnConnect` to be called before we
  // know that we're connected.

  // set a handler to get called when we're connected.
  client.on('connect', handleOnConnect(client));
}

main();
