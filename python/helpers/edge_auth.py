# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import datetime


class MqttEdgeAuth(object):
    def __init__(self) -> None:
        pass

    def renew(self) -> None:
        """
        Renew authorization. This casuses a new password string to be generated.
        """
        pass

    def get_expiry(self) -> datetime.datetime:
        """
        Get a datetime.datetime value for the expiry of the current credentials.
        """
        pass

    def get_client_id(self) -> str:
        """
        Get the client_id value used for creating the MQTT session
        """
        pass

    def get_username(self) -> str:
        """
        Get the username to pass into the MQTT CONNECT packet
        """
        pass

    def gat_password(self) -> str:
        """
        Get the password to pass into the MQTT CONNECT passoed
        """
        pass

    def get_hostname(self) -> str:
        """
        Get the hostname to connect the MQTT transport to
        """
        pass

    def get_server_verification_cert(self) -> str:
        """
        Get the verification cert used to verify the TLS connection that the MQTT transport uses
        """
        pass
