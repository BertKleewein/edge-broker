# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
from paho.mqtt import client as mqtt
from symmetric_key_auth import SymmetricKeyAuth
from helper_objects import (
    IncomingMessageList,
    IncomingAckList,
    ConnectionStatus,
)
from typing import Any

logger = logging.getLogger(__name__)


class SampleAppBase(object):
    def __init__(self) -> None:
        self.mqtt_client: mqtt.Client = None
        self.auth: SymmetricKeyAuth = None
        self.connection_status = ConnectionStatus()
        self.incoming_subacks = IncomingAckList()
        self.incoming_pubacks = IncomingAckList()
        self.incoming_messages = IncomingMessageList()

    def handle_on_connect(
        self, mqtt_client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        logger.info(
            "handle_on_connect called with status='{}'".format(
                mqtt.connack_string(rc)
            )
        )

        # In Paho thread.  Save what we need and return.
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.connection_status.connected = True
        else:
            self.connection_status.disconnected_error = Exception(
                mqtt.connack_string(rc)
            )

    def handle_on_disconnect(
        self, client: mqtt.Client, userdata: Any, rc: int
    ) -> None:
        # In Paho thread.  Save what we need and return.
        logger.info(
            "handle_on_disconnect called with error='{}'".format(
                mqtt.error_string(rc)
            )
        )
        self.connection_status.connected = False

    def handle_on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        granted_qos: int,
        properties: Any = None,
    ) -> None:
        # In Paho thread.  Save what we need and return.
        logger.info("Received SUBACK for mid {}".format(mid))
        self.incoming_subacks.add_item(mid, granted_qos)

    def handle_on_publish(
        self, client: mqtt.Client, userdata: Any, mid: int
    ) -> None:
        # In Paho thread.  Save what we need and return.
        logger.info("Received PUBACK for mid {}".format(mid))
        self.incoming_pubacks.add_item(mid, mid)

    def handle_on_message(
        self, mqtt_client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        # In Paho thread.  Save what we need and return.
        print("received message on {}".format(message.topic))
        self.incoming_messages.add_item(message)

    def create_mqtt_client(
        self, connection_string: str, clean_session: bool = False
    ) -> None:
        self.auth = SymmetricKeyAuth.create_from_connection_string(
            connection_string
        )
        self.mqtt_client = mqtt.Client(
            self.auth.client_id, clean_session=clean_session
        )
        self.mqtt_client.enable_logger()
        self.mqtt_client.username_pw_set(self.auth.username, self.auth.password)
        self.mqtt_client.tls_set_context(self.auth.create_tls_context())

        self.mqtt_client.on_connect = self.handle_on_connect
        self.mqtt_client.on_disconnect = self.handle_on_disconnect
        self.mqtt_client.on_subscribe = self.handle_on_subscribe
        self.mqtt_client.on_publish = self.handle_on_publish
        self.mqtt_client.on_message = self.handle_on_message

    def start_connect(self) -> None:
        self.mqtt_client.loop_start()
        self.mqtt_client.connect(self.auth.hostname, self.auth.port)

    def disconnect(self) -> None:
        self.mqtt_client.disconnect()
