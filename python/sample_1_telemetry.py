# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import os
import sys
from paho.mqtt import client as mqtt
from helpers import SymmetricKeyAuth, Message, topic_builder
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
        self.connected = threading.Event()

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

    def send_telemetry(self) -> None:
        messages_to_send = 20

        # keep track of all our messages
        outstanding_messages = []

        for i in range(0, messages_to_send):
            logger.info("Sending telemetry {}".format(i))

            # Make a message
            payload = {"index": i, "text": "This is message # {}".format(i)}
            msg = Message(payload)

            # Get our telemetry topic
            telemetry_topic = topic_builder.build_telemetry_publish_topic(
                self.auth.device_id, self.auth.module_id, msg
            )

            # publish.  Don't wait for the PUBACK
            mi = self.mqtt_client.publish(
                telemetry_topic, msg.get_binary_payload(), qos=1
            )

            # Remember the message info for later
            outstanding_messages.append(mi)

        # Now go through and wait for everything to publish.
        for mi in outstanding_messages:
            mi.wait_for_publish()

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

        self.send_telemetry()

        self.mqtt_client.disconnect()

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
