# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import time
import paho
from helpers import mqtt_edge_auth
from typing import Any

# SAMPLE 1
#
# Demonstrates how to connect to IoT Edge as a module and disconnect again.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleApp(object):
    def __init__(self) -> None:
        self._mqtt_client: paho.mqtt.client.Client = None
        self._auth: mqtt_edge_auth.MqttEdgeAuth = None
        self._connected = threading.Event()

    def handle_on_connect(self, userdata: Any, flags: Any, rc: int) -> None:
        logger.info(
            "handle_on_connect called with rc={} ({})".format(
                rc, paho.mqtt.client.connack_string(rc)
            )
        )
        # Set an event when we're connected so our main thread can continue
        if rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
            self._connected.set()

    def main(self) -> None:
        logger.info("Azure IoT Edge Protocol Translation Module (PTM) Sample")

        # Create an auth object which can help us get the credentials we need
        # in order to connect
        self._auth = mqtt_edge_auth.MqttEdgeAuth.create_from_environment()

        # Create an MQTT client object, passing in the credentials we
        # get from the auth object
        self._mqtt_client = paho.mqtt.client.Client(self._auth.client_id)
        self._mqtt_client.username_pw_set(
            self._auth.username, self._auth.password
        )
        # In this sample, we use the TLS context that the auth object builds for
        # us.  We could also build our own from the contents of the auth object
        self._mqtt_client.tls_set_context(self._auth.tls_context)

        # set a handler to get called when we're connected.
        self._mqtt_client.on_connect = self.handle_on_connect

        logger.info("Connecting")
        # Start the paho loop.
        self._mqtt_client.loop_start()
        # Connect.  When this returns, we're not actually connected yet.
        # We have to wait for `handle_on_connect` to be called before we
        # know that we're connected.
        self._mqtt_client.connect(self._auth.hostname, self._auth.port)

        # wait for the connectoin, but don't wait too long
        if not self._connected.wait(timeout=20):
            logger.error("Failed to connect.")

        else:

            # if `self._connected` was set, we know that we're connected.
            # sleep for a litle while, then disconnect.
            logger.info("sleeping...")
            time.sleep(20)
            logger.info("Disconecting")
            self._mqtt_client.disconnect()
            # `disconnect` is more immediate than `connect`.  We know
            # that we're disconnected at this point.

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
