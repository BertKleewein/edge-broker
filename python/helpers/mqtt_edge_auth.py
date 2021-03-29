# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import datetime
import ssl
from typing import Any


class MqttEdgeAuth(object):
    def __init__(self) -> None:
        self.token_expiry: datetime.datetime = None
        self.client_id: str = None
        self.username: str = None
        self.password: str = None
        self.hostname: str = None
        self.server_verification_cert: str = None
        self.device_id: str = None
        self.module_id: str = None
        self.port: int = 8883

    @classmethod
    def create_from_environment(
        cls, token_renewal_interval: int = 3600, token_renewal_margin: int = 300
    ) -> Any:
        """
        create a new Edge auth object from the environment.

        :param int token_renewal_interval: Number of seconds that SAS tokens created by
            this obhject will be valid.
        :param int token_renewal_margen: Number of seconds to subtract from
            `token_renewal_inteavral` when calculating the `token_expiry` time.

        :returns: MqttEdgeAuth object created by this function.
        """
        pass

    def renew_token(self) -> None:
        """
        Renew authorization. This casuses a new password string to be generated.
        """
        pass

    def create_tls_context(self) -> ssl.SSLContext:
        """
        Create an SSLContext object based on this object.

        :returns: SSLContext object
        """
        pass
