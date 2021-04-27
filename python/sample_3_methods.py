# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import os
import sys
import time
from paho.mqtt import client as mqtt
from helpers import (
    SymmetricKeyAuth,
    IncomingMessageList,
    WaitableDict,
    topic_builder,
    topic_parser,
)
from typing import Any

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

    def subscribe_for_methods(self) -> None:
        (rc, mid) = self.mqtt_client.subscribe(
            topic_builder.build_method_request_subscribe_topic(
                self.auth.device_id, self.auth.module_id
            ),
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

        self.subscribe_for_methods()

        end_time = time.time() + 600
        while time.time() < end_time:
            # Wait for any messages to show up.  Don't pop them.
            if self.incoming_messages.wait_for_message(end_time - time.time()):

                # Do we have any methods named "Ping"?  Pop it, with timeout=0 so it returns
                # immediately.  It returns None we don't have any matches.
                ping = self.incoming_messages.pop_next_method_request(
                    method_name="ping", timeout=0
                )
                if ping:
                    print("ping: {}".format(str(ping.payload)))
                    response_topic = topic_builder.build_method_response_publish_topic(
                        ping.topic, "200"
                    )
                    mi = self.mqtt_client.publish(
                        topic=response_topic, payload=ping.payload, qos=1
                    )
                    mi.wait_for_publish()
                    print("ping response sent")

                # Can also get all method requests with one call and use extract_method_name
                # to build a switch
                method_request = self.incoming_messages.pop_next_method_request(
                    timeout=0
                )
                if method_request:
                    print(
                        "method request: {}".format(str(method_request.payload))
                    )
                    print(
                        "method name: {}".format(
                            topic_parser.extract_method_name(
                                method_request.topic
                            )
                        )
                    )

                # Or maybe we get a message on some unkonwn topic.  We can get that too and use
                # topic_match.py or topic_parser.py to figure out where to make it go.
                undefined = self.incoming_messages.pop_next_message(timeout=0)
                if undefined:
                    print(
                        "Undefined: {}, {}".format(
                            undefined.topic, str(undefined.payload)
                        )
                    )

        self.mqtt_client.disconnect()

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
