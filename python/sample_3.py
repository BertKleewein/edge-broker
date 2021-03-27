# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
import threading
import paho
import datetime
import time
from helpers import mqtt_edge_auth
from typing import Any

# SAMPLE 1
#
# Demonstrates how to handle token renewal with IoT Edge connetions.
# Can also be applied to connections based on symmetric key and connection string.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleApp(object):
    def __init__(self) -> None:
        self._mqtt_client: paho.mqtt.client.Client = None
        self._auth: mqtt_edge_auth.MqttEdgeAuth = None
        self._connected = threading.Event()
        self._token_expiry_timer: threading.Timer = None

    def set_sas_token_expiry_timer(self) -> None:
        # If there is an old renewal timer, cancel it
        if self._token_expiry_timer:
            self._token_expiry_timer.cancel()

        # Calculate how many seconds in the future we need to renew the token
        seconds_until_renewal = (
            self._auth.token_expiry - datetime.datetime.now()
        ).total_seconds()

        # Set a new timer.  Be sure to set daemon=True so this timer doesn't prevent us from
        # exiting the app.
        self._token_expiry_timer = threading.Timer(
            seconds_until_renewal, self.renew_sas_token, daemon=True
        )

        logger.info(
            "SAS token renwal timer set for {} seconds in the future, at approximately {}".format(
                seconds_until_renewal, self._auth.token_expiry
            )
        )

    def renew_sas_token(self) -> None:
        logger.info("Renewing sas token and reconnecting")

        # Calculate the new token value
        self._auth.renew_token()

        # Set the new MQTT auth parameters
        self._mqtt_client.username_pw_set(
            self._auth.username, self._auth.password
        )

        # Reconect the client.  (This actually just disconnects it and lets Paho's automatic
        # reconnect connect again.)
        self._mqtt_client.reconnect()

        # Set a timer to renew the token at some point in the future.
        self.set_sas_token_expiry_timer()

    def handle_on_connect(self, userdata: Any, flags: Any, rc: int) -> None:
        logger.info(
            "handle_on_connect called with rc={} ({})".format(
                rc, paho.mqtt.client.connack_string(rc)
            )
        )

        if rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
            self._connected.set()
        elif rc == paho.mqtt.client.MQTT_ERR_NO_CONN:
            # If the connection dropped and our token is expired, renew the token and
            # reconnect.  Even though we have a timer to renew the token, that timer
            # might not fire correctly, especially if the system was asleep.
            if datetime.datetime.now() > self._auth.token_expiry:
                self.renew_sas_token()

    def main(self) -> None:
        logger.info("Azure IoT Edge Protocol Translation Module (PTM) Sample")

        # For testing purposes, set the SAS token to be valid for 10 minutes (using
        # `token_renewal_interal`) with the expiry happeing after 9 minutes (using
        # `token_renewal_interval - token_renewal_margin`).
        #
        # Don't do this in production.  For that, default values should be sufficient.
        #
        self._auth = mqtt_edge_auth.MqttEdgeAuth.create_from_environment(
            token_renewal_interval=600, token_renewal_margin=60
        )

        self._mqtt_client = paho.mqtt.client.Client(self._auth.client_id)
        self._mqtt_client.username_pw_set(
            self._auth.username, self._auth.password
        )
        self._mqtt_client.tls_set_context(self._auth.tls_context)
        self._mqtt_client.on_connect = self.handle_on_connect

        logger.info("Connecting")
        self._mqtt_client.connect(self._auth.hostname, self._auth.port)
        self.set_sas_token_expiry_timer()

        if not self._connected.wait(timeout=20):
            logger.error("Failed to connect.")
        else:
            logger.info("sleeping")
            time.sleep(7200)

        logger.info("Exiting.")


if __name__ == "__main__":
    SampleApp().main()
