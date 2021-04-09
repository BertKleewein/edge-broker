// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import * as uuid from 'uuid';

type TopicProperties = {value: string}

class IoTHubTwinTopicHelper {
  private _deviceIdForPublish: string;
  private _moduleIdForPublish: string;

  constructor () {
    this._deviceIdForPublish = '';
    this._moduleIdForPublish = '';
  }

  getResponseTopicForSubscribe(): string {
    throw new Error('Not implemented');
  }

  getPatchDesiredTopicForSubscribe(): string {
    throw new Error('Not implemented');
  }

  isResponseTopic(deviceId: string, moduleId: string, requestId: string, requestTopic: string) {
    throw new Error('Not implemented');
  }

  getOneTimeRequestTopicForPublish(vert: string, resource: string, deviceId: string, moduleId: string, properties: TopicProperties) {
    throw new Error('Not implemented');
  }
}

class IoTHubC2DTopicHelper {
  constructor() {}

  getTopicForSubscribe(): string {
    throw new Error('Not implemented');
  }

  isTopic(topic: string, deviceId: string, moduleId: string) {
    throw new Error('Not implemented');
  }
}

class IoTHubMethodTopicHelper {
  constructor() {}

  getMethodReceivedTopicForSubscribe(): string {
    throw new Error('Not implemented');
  }

  isMethodRequestTopic(): boolean {
    throw new Error('Not implemented');
  }

  getMethodResponseTopicForPublish(requestTopic: string, resultCode: string): string {
    throw new Error('Not implemented');
  }


}

export class IoTHubTopicHelper {
  private _defaultDeviceId:string;
  private _defaultModuleId:string;
  
  deviceId: string;
  moduleId: string;

  twin: IoTHubTwinTopicHelper;
  c2d: IoTHubC2DTopicHelper;
  method: IoTHubMethodTopicHelper;
  
  constructor(defaultDeviceId?: string, defaultModuleId?: string) {
    this._defaultDeviceId = defaultDeviceId || uuid.v4();
    this._defaultModuleId = defaultModuleId || uuid.v4();

    this.deviceId = '';
    this.moduleId = '';

    this.twin = new IoTHubTwinTopicHelper();
    this.c2d = new IoTHubC2DTopicHelper();
    this.method = new IoTHubMethodTopicHelper();
  }

  getDeviceIdForPublish(deviceId: string): string {
    return deviceId || this.deviceId || this._defaultDeviceId;
  }

  getModuleIdForPublish(moduleId: string): string {
    return moduleId || this.moduleId || this._defaultModuleId;
  }

  getTelemetryTopicForPublish(deviceId: string, moduleId: string, properties: TopicProperties): string {
    throw new Error('Not implemented');
  }
}