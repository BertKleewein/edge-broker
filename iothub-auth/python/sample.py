# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import os
import sys
import time
from paho.mqtt import client as mqtt
from symmetric_key_auth import SymmetricKeyAuth
from incoming_message_list import IncomingMessageList
from incoming_ack_list import IncomingAckList
from connection_status import ConnectionStatus
from typing import Any

# SAMPLE 1
#
# Demonstrates how to send telemetry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


class SampleApp(object):
    def __init__(self) -> None:
        self.mqtt_client: mqtt.Client = None
        self.auth: SymmetricKeyAuth = None
        self.connection_status = ConnectionStatus()
        self.incoming_subacks: IncomingAckList()
        self.incoming_messages = IncomingMessageList()

    def handle_on_connect(
        self, mqtt_client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        # Set an event when we're connected so our main thread can continue
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.connected.set()

    def handle_on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        granted_qos: int,
        properties: Any = None,
    ) -> None:
        # we're inside a Paho thread here.
        # Save the results and return as quickly as possible
        logger.info("Received SUBACK for mid {}".format(mid))
        self.incoming_subacks.add_item(mid, granted_qos)

    def subscribe_for_c2d(self) -> None:
        (rc, mid) = self.mqtt_client.subscribe(
            topic_builder.build_c2d_subscribe_topic(
                self.auth.device_id, self.auth.module_id
            ),
            1,
        )
        if rc:
            raise Exception("subscribe RC = {}".format(rc))
        print("send SUBSCRIBE for mid {}".format(mid))
        # wait for the suback.
        self.incoming_subacks.get_next_item(mid, timeout=10)
        print("SUBACK received for mid {}".format(mid))

    def handle_on_message(
        self, mqtt_client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        # we're inside a Paho thread here.
        # Save the message and return as quickly as possible
        print("received message on {}".format(message.topic))
        self.incoming_messages.add_item(message)

    def main(self) -> None:
        logger.info("Azure IoT Edge Protocol Translation Module (PTM) Sample")

        # Copy/paste code from other sample
        self.auth = SymmetricKeyAuth.create_from_connection_string(
            os.environ["IOTHUB_DEVICE_CONNECTION_STRING"]
        )
        self.mqtt_client = mqtt.Client(self.auth.client_id)
        self.mqtt_client.enable_logger()
        self.mqtt_client.username_pw_set(self.auth.username, self.auth.password)
        self.mqtt_client.tls_set_context(self.auth.create_tls_context())
        self.mqtt_client.on_connect = self.handle_on_connect
        self.mqtt_client.loop_start()
        self.mqtt_client.connect(self.auth.hostname, self.auth.port)
        if not self.connected.wait(timeout=20):
            logger.error("Failed to connect.")
            sys.exit(1)

        # Paho callsbacks for PUBACK and SUBACK
        self.mqtt_client.on_subscribe = self.handle_on_subscribe
        self.mqtt_client.on_message = self.handle_on_message

        self.subscribe_for_c2d()

        end_time = time.time() + 600
        while time.time() < end_time:
            c2d = self.incoming_messages.pop_next_c2d(
                timeout=end_time - time.time()
            )
            if c2d:
                print("C2d: {}".format(str(c2d.payload)))

        self.mqtt_client.disconnect()

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
