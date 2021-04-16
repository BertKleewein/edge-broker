# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import ssl
import abc
import threading
import time
import weakref
import logging
from typing import Callable
from . import sas_token, constants

logger = logging.getLogger(__name__)

sas_token_renewed_handler = Callable[[], None]

# TODO: what about websockets?  Does port belong here?  Transport?  if not here, where?


def format_sas_uri(hostname: str, device_id: str, module_id: str) -> str:
    if module_id:
        return "{}/devices/{}/modules/{}".format(hostname, device_id, module_id)
    else:
        return "{}/devices/{}".format(hostname, device_id)


class AuthorizationBase(abc.ABC):
    def __init__(self) -> None:
        self.hostname: str = None
        self.device_id: str = None
        self.module_id: str = None
        self.port: int = 8883
        self.api_version: str = constants.IOTHUB_API_VERSION
        self.gateway_host_name: str = None

    @property
    @abc.abstractmethod
    def password(self) -> str:
        pass

    @property
    def username(self) -> str:
        # TODO: add product_info stuff
        if self.module_id:
            return "{}/{}/{}/?api-version={}".format(
                self.hostname, self.device_id, self.module_id, self.api_version
            )
        else:
            return "{}/{}/?api-version={}".format(
                self.hostname, self.device_id, self.api_version
            )

    @property
    def client_id(self) -> str:
        if self.module_id:
            return "{}/{}".format(self.device_id, self.module_id)
        else:
            return self.device_id


class RenewableTokenAuthorizationBase(AuthorizationBase):
    def __init__(self) -> None:
        super(RenewableTokenAuthorizationBase, self).__init__()

        self.server_verification_cert: str = None
        self.sas_token: sas_token.RenewableSasToken = None
        self.sas_token_renewal_timer: threading.Timer = None
        self.on_sas_token_renewed: sas_token_renewed_handler = None

    @property
    def password(self) -> str:
        return str(self.sas_token)

    @property
    def sas_uri(self) -> str:
        return format_sas_uri(self.hostname, self.device_id, self.module_id)

    # TODO: rename token to sas_token in all method names
    @property
    def sas_token_expiry_time(self) -> int:
        return self.sas_token.expiry_time

    @property
    def sas_token_renewal_time(self) -> int:
        return (
            self.sas_token.expiry_time - constants.DEFAULT_TOKEN_RENEWAL_MARGIN
        )

    @property
    def sas_token_ready_to_renew(self) -> bool:
        return time.time() > self.sas_token_renewal_time

    @property
    def seconds_until_sas_token_renewal(self) -> int:
        return max(0, self.sas_token_renewal_time - int(time.time()))

    def cancel_sas_token_renewal_timer(self) -> None:
        if self.sas_token_renewal_timer:
            self.sas_token_renewal_timer.cancel()
            self.sas_token_renewal_timer = None

    def set_sas_token_renewal_timer(
        self, on_sas_token_renewed: sas_token_renewed_handler = None
    ) -> None:
        # If there is an old renewal timer, cancel it
        self.cancel_sas_token_renewal_timer()
        self.on_sas_token_renewed = on_sas_token_renewed

        # Use weak a weak reference to self so the timer doesn't prevent this object
        # from being collected.
        self_weakref = weakref.ref(self)

        def on_timer_expired() -> None:
            this = self_weakref()
            if this:
                this.sas_token_renewal_timer = None
                this.renew_sas_token()
            else:
                logger.info(
                    "Renewal timer triggered after TokenRenewalHelper already collected"
                )

        # Set a new timer.
        seconds_until_renewal = self.seconds_until_sas_token_renewal
        self.sas_token_renewal_timer = threading.Timer(
            seconds_until_renewal, self.renew_sas_token
        )
        self.sas_token_renewal_timer.daemon = True
        self.sas_token_renewal_timer.start()

        logger.info(
            "SAS token renwal timer set for {} seconds in the future, at approximately {}".format(
                seconds_until_renewal, self.sas_token_expiry_time
            )
        )

    def renew_sas_token(self) -> None:
        """
        Renew authorization. This casuses a new password string to be generated.
        """
        logger.info("Renewing sas token and reconnecting")

        # Cancel any timers that might be running.
        self.cancel_sas_token_renewal_timer()

        # Calculate the new token value
        self.sas_token.refresh()

        # notify
        if self.on_sas_token_renewed:
            self.on_sas_token_renewed()

    def create_tls_context(self) -> ssl.SSLContext:
        """
        Create an SSLContext object based on this object.

        :returns: SSLContext object
        """
        ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)
        if self.server_verification_cert:
            ssl_context.load_verify_locations(
                cadata=self.server_verification_cert
            )
        else:
            ssl_context.load_default_certs()

        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True

        return ssl_context
