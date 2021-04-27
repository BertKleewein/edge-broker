# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import os
import sys
import time
import json
from paho.mqtt import client as mqtt
from helpers import (
    SymmetricKeyAuth,
    IncomingMessageList,
    WaitableDict,
    topic_builder,
    topic_parser,
)
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


class SampleApp(object):
    def __init__(self) -> None:
        self.mqtt_client: mqtt.Client = None
        self.auth: SymmetricKeyAuth = None
        self.connected = threading.Event()
        self.incoming_subacks: WaitableDict[int, int] = WaitableDict()
        self.incoming_messages = IncomingMessageList()

    def handle_on_connect(
        self, mqtt_client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        logger.info(
            "handle_on_connect called with rc={} ({})".format(
                rc, mqtt.connack_string(rc)
            )
        )
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

    def subscribe_for_twins(self) -> None:
        (rc, mid) = self.mqtt_client.subscribe(
            [
                (
                    topic_builder.build_twin_response_subscribe_topic(
                        self.auth.device_id, self.auth.module_id
                    ),
                    1,
                ),
                (
                    topic_builder.build_twin_patch_desired_subscribe_topic(
                        self.auth.device_id, self.auth.module_id
                    ),
                    1,
                ),
            ],
            1,
        )
        if rc:
            raise Exception("subscribe RC = {}".format(rc))
        print("send SUBSCRIBE for mid {}".format(mid))
        self.incoming_subacks.get_next_item(mid, timeout=10)
        print("SUBACK received for mid {}".format(mid))

    def handle_on_message(
        self, mqtt_client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        # we're inside a Paho thread here.
        # Save the message and return as quickly as possible
        print("received message on {}".format(message.topic))
        self.incoming_messages.add_item(message)

    def get_twin(self) -> Dict[str, Any]:
        """
        Get the device twin
        """

        # Create a topic to publish our GET request.  This is a
        # onetime topic with a request ID built in.
        topic = topic_builder.build_twin_get_publish_topic(
            self.auth.device_id, self.auth.module_id
        )

        # publish it.
        mi = self.mqtt_client.publish(topic, qos=1)
        if mi.rc:
            raise Exception()

        # use pop_next_twin_response to wait for the response.
        # notice how request_topic is a parameter.  This is used
        # to wait for the response with the specific $rid.
        twin = self.incoming_messages.pop_next_twin_response(
            request_topic=topic, timeout=10
        )

        # That's it.  We have the Twin
        # TODO: this should use topic_parser.extract_status_code to make sure this didn't fail.
        if twin:
            twin = json.loads(twin.payload)
            print("Got twin = {}".format(twin))
            return twin  # type: ignore
        else:
            print("Error getting twin.")
            return None

    def patch_reported_properties(self, value: str) -> None:
        """
        Patch TWIN reported properties
        """

        # Make the patch
        patch = {"testObject": {"testValue": value}}

        # Build a topic for the PATCH request.
        topic = topic_builder.build_twin_patch_reported_publish_topic(
            self.auth.device_id, self.auth.module_id
        )

        # publish the patch
        mi = self.mqtt_client.publish(topic, json.dumps(patch), qos=1)
        if mi.rc:
            raise Exception()

        # Use pop_next_twin_response to get our response.
        patch_result = self.incoming_messages.pop_next_twin_response(
            request_topic=topic, timeout=10
        )

        print("patch_result = {}".format(patch_result))
        # TODO: use topic_parser.extract_status_code

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

        self.subscribe_for_twins()

        self.patch_reported_properties("shazam!")

        self.get_twin()

        end_time = time.time() + 600
        while time.time() < end_time:

            # wait for incoming patches
            patch = self.incoming_messages.pop_next_twin_patch_desired(
                timeout=end_time - time.time()
            )
            if patch:
                print("patch received: {}".format(str(patch.payload)))
                print(
                    "patch version: {}".format(
                        topic_parser.extract_twin_version(patch.topic)
                    )
                )

        self.mqtt_client.disconnect()

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
