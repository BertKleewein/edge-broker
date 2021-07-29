# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
from paho.mqtt import client as mqtt
from symmetric_key_auth import SymmetricKeyAuth
from mqtt_helpers import IncomingMessageList, IncomingAckList, ConnectionStatus
from typing import Any, Tuple

logger = logging.getLogger(__name__)


class PahoClient(object):
    def __init__(self, auth: SymmetricKeyAuth) -> None:
        self.mqtt_client: mqtt.Client = None
        self.auth: SymmetricKeyAuth = auth
        self.connection_status = ConnectionStatus()
        self.incoming_subacks = IncomingAckList()
        self.incoming_unsubacks = IncomingAckList()
        self.incoming_pubacks = IncomingAckList()
        self.incoming_messages = IncomingMessageList()

    @classmethod
    def error_string(cls, mqtt_errno: int) -> str:
        return mqtt.error_string(mqtt_errno)  # type: ignore

    @classmethod
    def create_from_auth(
        cls, auth: SymmetricKeyAuth, clean_session: bool = False
    ) -> Any:
        obj = cls(auth)
        obj.create_mqtt_client(clean_session)
        return obj

    @classmethod
    def create_from_connection_string(
        cls, connection_string: str, clean_session: bool = False
    ) -> Any:
        auth = SymmetricKeyAuth.create_from_connection_string(connection_string)
        return cls.create_from_auth(auth, clean_session)

    def _handle_on_connect(
        self, mqtt_client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        """
        event handler for Paho on_connect events.  Do not call directly.
        """
        logger.info(
            "_handle_on_connect called with status='{}'".format(
                mqtt.connack_string(rc)
            )
        )

        # In Paho thread.  Save what we need and return.
        if rc == mqtt.MQTT_ERR_SUCCESS:
            # causes code waiting in `self.connection_status.wait_for_connected` to return
            self.connection_status.connected = True
        else:
            # causes code waiting in `self.connection_status.wait_for_connected` to raise this exception
            # causes code waiting in `self.connection_status.wait_for_disconnected` to return
            self.connection_status.connection_error = Exception(
                mqtt.connack_string(rc)
            )

    def _handle_on_disconnect(
        self, client: mqtt.Client, userdata: Any, rc: int
    ) -> None:
        """
        event handler for Paho on_disconnect events.  Do not call directly.
        """
        # In Paho thread.  Save what we need and return.
        logger.info(
            "_handle_on_disconnect called with error='{}'".format(
                mqtt.error_string(rc)
            )
        )
        # causes code waiting in `self.connection_status.wait_for_disconnected` to raise this exception
        self.connection_status.connected = False

    def _handle_on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        granted_qos: int,
        properties: Any = None,
    ) -> None:
        """
        event handler for Paho on_subscribe events.  Do not call directly.
        """
        # In Paho thread.  Save what we need and return.
        logger.info("Received SUBACK for mid {}".format(mid))
        # causes code waiting for this mid via `self.incoming_subacks.wait_for_ack` to return
        self.incoming_subacks.add_ack(mid, granted_qos)

    def _handle_on_unsubscribe(
        self, client: mqtt.Client, userdata: Any, mid: int
    ) -> None:
        """
        event handler for Paho on_unsubscribe events.  Do not call directly.
        """
        # In Paho thread.  Save what we need and return.
        logger.info("Received UNSUBACK for mid {}".format(mid))
        # causes code waiting for this mid via `self.incoming_unsubacks.wait_for_ack` to return
        self.incoming_unsubacks.add_ack(mid, mid)

    def _handle_on_publish(
        self, client: mqtt.Client, userdata: Any, mid: int
    ) -> None:
        """
        event handler for Paho on_publish events.  Do not call directly.
        """
        # In Paho thread.  Save what we need and return.
        logger.info("Received PUBACK for mid {}".format(mid))
        # causes code waiting for this mid via `self.incoming_pubacks.wait_for_ack` to return
        self.incoming_pubacks.add_ack(mid, mid)

    def _handle_on_message(
        self, mqtt_client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        """
        event handler for Paho on_message events.  Do not call directly.
        """
        # In Paho thread.  Save what we need and return.
        print("received message on {}".format(message.topic))
        # causes code waiting for messages via `self.incoming_messages.wait_for_message` and
        # `self.incoming_messages.pop_next_message` to return.
        self.incoming_messages.add_message(message)

    def create_mqtt_client(self, clean_session: bool = False) -> None:
        """
        Create a Paho MQTT client object to use for communicating
        with the server and store it in `self.mqtt_client`.
        """
        self.mqtt_client = mqtt.Client(
            self.auth.client_id, clean_session=clean_session
        )
        self.mqtt_client.enable_logger()
        self.mqtt_client.username_pw_set(self.auth.username, self.auth.password)
        self.mqtt_client.tls_set_context(self.auth.create_tls_context())

        self.mqtt_client.on_connect = self._handle_on_connect
        self.mqtt_client.on_disconnect = self._handle_on_disconnect
        self.mqtt_client.on_subscribe = self._handle_on_subscribe
        self.mqtt_client.on_publish = self._handle_on_publish
        self.mqtt_client.on_message = self._handle_on_message

    def start_connect(self) -> None:
        """
        Start connecting to the server.  Returns after the CONNECT packet has been sent.
        Connection isn't established until `self._handle_on_connect` has been called and
        `self.connection_status.connected` is `True`.
        """
        self.mqtt_client.loop_start()
        self.mqtt_client.connect(self.auth.hostname, self.auth.port)

    def disconnect(self) -> None:
        """
        Disconnect from the server.  Disconnection is likely complete after this function
        returns, but it is more reliable to wait for `self.connection_status.connected` to be
        set to `False`.
        """
        self.mqtt_client.disconnect()

    def publish(
        self,
        topic: str,
        payload: Any = None,
        qos: int = 0,
        retain: bool = False,
    ) -> Tuple[int, int]:
        return self.mqtt_client.publish(  # type: ignore
            topic, payload, qos, retain
        )

    def subscribe(self, topic: str, qos: int = 0) -> Tuple[int, int]:
        return self.mqtt_client.subscribe(topic, qos)  # type: ignore

    def unsubscribe(self, topic: str) -> Tuple[int, int]:
        return self.mqtt_client.unsubscribe(topic)  # type: ignore
