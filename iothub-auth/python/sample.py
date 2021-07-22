# Copyright (c) Microsoft Corporation. All rights reserved.S
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import os
import sys
import logging
import json
import time
from sample_base import SampleAppBase
from paho.mqtt import client as mqtt

logger = logging.getLogger(__name__)

"""
Uncomment the following lines to enable debug logging
"""

logging.basicConfig(level=logging.INFO)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


class SampleApp(SampleAppBase):
    def __init__(self) -> None:
        super(SampleApp, self).__init__()

    def sample_connect_and_disconenct(self) -> None:
        """
        Demonstrates how to connect and disconnect from iothub
        """

        self.create_mqtt_client(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Starting connection")
        self.start_connect()

        print("Waiting for CONNACK")
        if not self.connection_status.wait_for_connected(timeout=20):
            print("failed to connect.  exiting")
            sys.exit(1)

        print("CONNACK received.  Disconnecting")
        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def sample_connect_and_disconnect_clean_session(self) -> None:
        """
        Demonstrates how to connect and disconnect from iothub with clean-session=True
        """

        self.create_mqtt_client(
            os.environ["IOTHUB_CONNECTION_STRING"], clean_session=True
        )

        print("Starting connection")
        self.start_connect()

        print("Waiting for CONNACK")
        if not self.connection_status.wait_for_connected(timeout=20):
            print("failed to connect.  exiting")
            sys.exit(1)

        print("CONNACK received.  Disconnecting")
        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def sample_publish_with_qos_0(self) -> None:
        """
        Demonstrates how to publish at QOS 0
        """
        self.create_mqtt_client(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Connecting")
        self.start_connect()
        if not self.connection_status.wait_for_connected(timeout=20):
            sys.exit(1)

        topic = "/vehicles/V1/GPS"
        payload = {
            "latitude": 47.63962283908785,
            "longitude": -122.12718926895407,
        }
        print("Publishing to {} at QOS=0".format(topic))
        message_info = self.mqtt_client.publish(
            topic, json.dumps(payload), qos=1
        )

        print(
            "Publish returned rc={}: {}".format(
                message_info.rc, mqtt.error_string(message_info.rc)
            )
        )

        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def sample_publish_with_qos_1(self) -> None:
        """
        Demonstrates how to publish at QOS 1
        """
        self.create_mqtt_client(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Connecting")
        self.start_connect()
        if not self.connection_status.wait_for_connected(timeout=20):
            sys.exit(1)

        topic = "/vehicles/V1/GPS"
        payload = {
            "latitude": 47.63962283908785,
            "longitude": -122.12718926895407,
        }
        print("Publishing to {} at QOS=1".format(topic))
        (rc, mid) = self.mqtt_client.publish(topic, json.dumps(payload), qos=1)

        print("Publish returned rc={}: {}".format(rc, mqtt.error_string(rc)))
        print("Waiting for PUBACK for mid={}".format(mid))

        # Note: Paho will queue the PUBLISH even if an error is returned, so it's still
        # possible to receive a PUBACK in that case if, for instance, Paho is able to
        # reconnect and then PUBLISH some time in the future.

        if self.incoming_pubacks.wait_for_item(mid, timeout=20):
            print("PUBACK received")
        else:
            print("PUBACK not received within 20 seconds")

        print("Disconnecting")
        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def sample_subscribe(self) -> None:
        """
        Demonstrates how to subscribe to a topic and receive messages on that topic
        """
        self.create_mqtt_client(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Connecting")
        self.start_connect()
        if not self.connection_status.wait_for_connected(timeout=20):
            sys.exit(1)

        topic_filter = "/vehicles/+/GPS/#"
        qos = 1
        print("Subscribing to {} at qos {}".format(topic_filter, qos))
        (rc, mid) = self.mqtt_client.subscribe(topic_filter, qos)

        # Note: If an error is returned, Paho will not queue the subscribe. 3dd Paho will also not
        # retry the SUBSCRIBE if we don't receive a SUBACK.  The only way to know for sure
        # that the subscription was successful is to watch for the SUBACK.

        print("Waiting for SUBACK for mid={}".format(mid))
        if self.incoming_subacks.wait_for_item(mid, timeout=20):
            print("SUBACK received")
        else:
            print("SUBACK not received within 20 seconds")

        print("Disconnecting")
        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def sample_receive_messages(self) -> None:
        """
        Demonstrates how to receive messages on a topic
        """
        self.create_mqtt_client(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Connecting")
        self.start_connect()
        if not self.connection_status.wait_for_connected(timeout=20):
            sys.exit(1)

        topic_filter = "/vehicles/+/GPS/#"
        qos = 1
        print("Subscribing to {} at qos {}".format(topic_filter, qos))
        (rc, mid) = self.mqtt_client.subscribe(topic_filter, qos)

        if self.incoming_subacks.wait_for_item(mid, timeout=20):
            print("SUBACK received")
        else:
            print("SUBACK not received within 20 seconds")
            self.disconnect()
            self.connection_status.wait_for_disconnected()
            return

        time_to_listen = 120
        end_time = time.time() + time_to_listen

        while time.time() <= end_time:
            remaining_time = end_time - time.time()
            print(
                "Waiting for messages for {} more seconds".format(
                    remaining_time
                )
            )

            message = self.incoming_messages.pop_next_message(
                timeout=remaining_time
            )
            if message:
                # message.topic is a string, do we don't need to convert
                print("Message received on topic {}".format(message.topic))

                # message.payload might be a byte array or it might be a string.
                # Make sure we have a string to work with
                try:
                    # convert from `bytes` to `str`
                    payload_string = message.payload.decode("utf-8")
                    print("payload is a byte array")
                except AttributeError:  # probably "'str' object has no attribute 'decode'"
                    payload_string = message.payload
                    print("payload is a string")

                # if our payload is json and we want to convert from a string to an object, do this:
                try:
                    payload_object = json.loads(payload_string)
                    print("Payload is valid JSON: {}".format(payload_object))
                except json.decoder.JSONDecodeError:
                    print(
                        "Payload is not valid JSON: {}".format(payload_string)
                    )

        print("Disconnecting")
        self.disconnect()
        self.connection_status.wait_for_disconnected()

    def main(self) -> None:
        # Call any of the sample_* functions here
        self.sample_receive_messages()


if __name__ == "__main__":
    SampleApp().main()
