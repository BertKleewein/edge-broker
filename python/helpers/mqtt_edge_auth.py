# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import datetime
import ssl
from typing import Any


class MqttEdgeAuth(object):
    def __init__(self) -> None:
        self.expiry: datetime.datetime = None
        self.client_id: str = None
        self.username: str = None
        self.password: str = None
        self.hostname: str = None
        self.server_verification_cert: str = None
        self.tls_context: ssl.SSLContext = None
        self.device_id: str = None
        self.module_id: str = None
        self.port: int = 8883

    @classmethod
    def create_from_environment(cls) -> Any:
        """
        create a new Edge auth object from the environment.
        """
        pass

    def renew(self) -> None:
        """
        Renew authorization. This casuses a new password string to be generated.
        """
        pass
