// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

const PORT = 8888;
const HOST = 'host';
const KEY = 'path_to_key';
const CERT = 'path_to_cert';
const TRUSTED_CA_LIST = 'list';

interface MqttEdgeAuthParams {
  port : number;
  host : string;
  key : string;
  cert : string;
  rejectUnauthorized : boolean;
  ca : string;
  deviceId : string;
  moduleId : string;
}

export class MqttEdgeAuth {
  port : number;
  host : string;
  key : string;
  cert : string;
  rejectUnauthorized : boolean;
  ca : string;
  deviceId : string;
  moduleId : string;

  constructor(input: MqttEdgeAuthParams) {
    this.port = input.port;
    this.host = input.host;
    this.key = input.key;
    this.cert = input.cert;
    this.rejectUnauthorized = true;
    this.ca = input.ca;
    this.deviceId = input.deviceId;
    this.moduleId = input.moduleId;
  }

  static createFromEnvironment() {
    return new MqttEdgeAuth({
      port: PORT,
      host: HOST,
      key: KEY,
      cert: CERT,
      rejectUnauthorized: true,
      ca: TRUSTED_CA_LIST,
      moduleId: 'moduleId',
      deviceId: 'deviceId'
    }) ;
  }
}