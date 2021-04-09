// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import * as mqtt from 'mqtt';
import { IClientOptions } from 'mqtt';
import {MqttEdgeAuth, IoTHubTopicHelper} from '../helpers';
import * as sensor from 'node-dht-sensor';

// SAMPLE 2
//
// Demonstrates how to connect to IoT Edge as a module and use identity translation
// to send telemetry.

const AUTHORIZED_DEVICES = JSON.parse(process.env.AUTHORIZED_DEVICES || '');

export class SampleApp {
  private _mqtt_client: mqtt.Client | undefined;
  private _topic_helper;
  private _auth;

  constructor() {
    this._auth = MqttEdgeAuth.createFromEnvironment();
    this._topic_helper = new IoTHubTopicHelper(this._auth.deviceId, this._auth.moduleId);
  }

  main() {
    console.log('Azure IoT Edge Protocol Translation Module (PTM) Sample');
    // In this sample, we use the TLS context that the auth object builds for
    // us.  We could also build our own from the contents of the auth object
    let options: IClientOptions = this._auth;
    options.protocol = 'mqtts';
    // wait for the connection, but don't wait too long
    options.connectTimeout = 30 * 1000;
  
    const topicHelper = new IoTHubTopicHelper(this._auth.deviceId, this._auth.moduleId)
    console.log("Connecting");
    // Create an MQTT client object, passing in the credentials we
    // get from the auth object
    const client  = mqtt.connect(options);
    // Connect. When this returns, we're not actually connected yet.
    // We have to wait for `handleOnConnect` to be called before we
    // know that we're connected.
  
    // set a handler to get called when we're connected.
    client.on('connect', this.handleOnConnect(client));
    client.on('message', this.handleOnMessage(client));
  
    setInterval(this.sensorCallback(client), 2000);
  }

  handleOnConnect(client: mqtt.Client) {
    return function () {
      client.subscribe('presence'), function (err: any) {
        if (!err) {
          client.publish('presence', 'Hello mqtt')
        }
      }
    }
  }
  
  handleOnMessage(client: mqtt.Client) {
    return function (topic: any, message: Buffer) {
      console.log(message.toString());
    }
  }
  
  // https://github.com/momenso/node-dht-sensor
  sensorCallback(client: mqtt.Client) {
    const that = this;
    return function () {
      sensor.read(11, 4, function(err: Error, temperature: number, humidity: number) {
        if (err) {
          throw err;
        }
        const topic = that._topic_helper.getTelemetryTopicForPublish('', '', {})
        const message = `temp: ${temperature}°C, humidity: ${humidity}%`;
        client.publish(topic, message, {qos: 1})
      });
    }
  }
  

} 


new SampleApp().main();
