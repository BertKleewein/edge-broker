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
from track2 import (
    SymmetricKeyAuth,
    Message,
    IncomingMessageList,
    WaitableDict,
    topic_builder,
    topic_parser,
)
from typing import Any, List, Tuple, Union, Dict

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
        # Set an event when we're connected so our main thread can continue
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.connected.set()
        elif rc == mqtt.CONNACK_REFUSED_SERVER_UNAVAILABLE:
            # actually, server is available, but username is probably wrong
            pass
        elif rc == mqtt.MQTT_ERR_NO_CONN:
            # client_id or password is wrong.  Check the sas token expirey.  That's all we can do
            if self.auth.sas_token_ready_to_renew:
                self.auth.renew_sas_token()

        # TODO: how to handle connection failure?
        # TODO: thread safety

    def handle_sas_token_renewed(self) -> None:
        logger.info("handle_sas_token_renewed")

        # Set the new MQTT auth parameters
        self.mqtt_client.username_pw_set(self.auth.username, self.auth.password)

        # Reconect the client.  (This actually just disconnects it and lets Paho's automatic
        # reconnect connect again.)
        self.mqtt_client.reconnect()

        self.auth.set_sas_token_renewal_timer(self.handle_sas_token_renewed)

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

    def subscribe(
        self, topic: Union[str, List[Tuple[Any, int]]], qos: int = 0
    ) -> None:
        (rc, mid) = self.mqtt_client.subscribe(topic, qos)
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

    def remove_completed_messages(
        self, messages: List[mqtt.MQTTMessageInfo]
    ) -> List[mqtt.MQTTMessageInfo]:
        return [x for x in messages if not x.is_published()]

    def send_telemetry(self) -> None:
        messages_to_send = 20
        outstanding_messages = []
        start = time.time()
        for i in range(0, messages_to_send):
            logger.info("Sending telemetry {}".format(i))
            payload = {
                "index": i,
                "text": "Hello from sample_4.  This is message # {}".format(i),
            }
            msg = Message(payload)

            telemetry_topic = topic_builder.build_telemetry_publish_topic(
                self.auth.device_id, self.auth.module_id, msg
            )
            mi = self.mqtt_client.publish(
                telemetry_topic, msg.get_binary_payload(), qos=1
            )

            outstanding_messages.append(mi)
            outstanding_messages = self.remove_completed_messages(
                outstanding_messages
            )

            print(
                "{} sent, {} awaiting PUBACK".format(
                    i + 1, len(outstanding_messages)
                )
            )

        while len(outstanding_messages):
            print("Waiting for {} messages".format(len(outstanding_messages)))
            outstanding_messages[0].wait_for_publish()
            outstanding_messages = self.remove_completed_messages(
                outstanding_messages
            )
        end = time.time()

        print("Done sending telemetry.")
        print(
            "{} messages sent in {} seconds.  {} messages per second".format(
                messages_to_send, end - start, messages_to_send / (end - start)
            )
        )

    def subscribe_all(self) -> None:
        topics = [
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
            (
                topic_builder.build_method_request_subscribe_topic(
                    self.auth.device_id, self.auth.module_id
                ),
                1,
            ),
            (
                topic_builder.build_c2d_subscribe_topic(
                    self.auth.device_id, self.auth.module_id
                ),
                1,
            ),
        ]
        print("Subscribing to {}".format(topics))
        self.subscribe(topics)

    def get_twin(self) -> Dict[str, Any]:
        topic = topic_builder.build_twin_get_publish_topic(
            self.auth.device_id, self.auth.module_id
        )
        self.mqtt_client.publish(topic, qos=1)
        # todo wait on mi

        twin = self.incoming_messages.pop_next_twin_response(
            request_topic=topic, timeout=10
        )
        if twin:
            twin = json.loads(twin.payload)
            print("Got twin = {}".format(twin))
            return twin  # type: ignore
        else:
            print("Error getting twin.")
            return None

    def patch_reported_properties(self, value: str) -> None:
        patch = {"testObject": {"testValue": value}}
        topic = topic_builder.build_twin_patch_reported_publish_topic(
            self.auth.device_id, self.auth.module_id
        )
        # todo: easier way to test connection being forced closed: send invalid patch
        self.mqtt_client.publish(topic, json.dumps(patch), qos=1)
        # todo wait on mi

        patch_result = self.incoming_messages.pop_next_twin_response(
            request_topic=topic, timeout=10
        )
        # TODO: raise exception on error
        print("patch_result = {}".format(patch_result))

    def main(self) -> None:
        logger.info("Azure IoT Edge Protocol Translation Module (PTM) Sample")

        # Create an auth object which can help us get the credentials we need
        # in order to connect
        self.auth = SymmetricKeyAuth.create_from_connection_string(
            os.environ["IOTHUB_DEVICE_CONNECTION_STRING"]
        )
        self.auth.set_sas_token_renewal_timer(self.handle_sas_token_renewed)

        # Create an MQTT client object, passing in the credentials we
        # get from the auth object
        self.mqtt_client = mqtt.Client(self.auth.client_id)
        self.mqtt_client.enable_logger()
        self.mqtt_client.username_pw_set(self.auth.username, self.auth.password)
        # In this sample, we use the TLS context that the auth object builds for
        # us.  We could also build our own from the contents of the auth object
        self.mqtt_client.tls_set_context(self.auth.create_tls_context())

        # set a handler to get called when we're connected.
        self.mqtt_client.on_connect = self.handle_on_connect
        self.mqtt_client.on_subscribe = self.handle_on_subscribe
        self.mqtt_client.on_message = self.handle_on_message

        logger.info("Connecting")
        # Start the paho loop.
        self.mqtt_client.loop_start()
        # Connect.  When this returns, we're not actually connected yet.
        # We have to wait for `handle_on_connect` to be called before we
        # know that we're connected.
        self.mqtt_client.connect(self.auth.hostname, self.auth.port)

        # wait for the connectoin, but don't wait too long
        if not self.connected.wait(timeout=20):
            logger.error("Failed to connect.")
            sys.exit(1)

        self.subscribe_all()
        self.send_telemetry()
        self.patch_reported_properties("shazam!")
        self.get_twin()

        start_time = time.time()
        end_time = start_time + 600
        while time.time() < end_time:
            if self.incoming_messages.wait_for_message(end_time - time.time()):

                c2d = self.incoming_messages.pop_next_c2d(timeout=0)
                if c2d:
                    print("C2d: {}".format(str(c2d.payload)))

                twin_patch = self.incoming_messages.pop_next_twin_patch_desired(
                    timeout=0
                )
                if twin_patch:
                    print("twin patch: {}".format(str(twin_patch.payload)))
                    print(
                        "twin version: {}".format(
                            topic_parser.extract_twin_version(twin_patch.topic)
                        )
                    )

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

                fail = self.incoming_messages.pop_next_method_request(
                    method_name="fail", timeout=0
                )
                if fail:
                    print("fail: {}".format(str(fail.payload)))
                    response_topic = topic_builder.build_method_response_publish_topic(
                        fail.topic, "400"
                    )
                    mi = self.mqtt_client.publish(
                        topic=response_topic, payload=fail.payload, qos=1
                    )
                    mi.wait_for_publish()
                    print("fail response sent")

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
