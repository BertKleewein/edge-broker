# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import abc
import threading
import time
import logging
import ssl
from typing import Any, Callable, Dict
from ... import constants, version_compat
from .. import hmac_signing_mechanism, connection_string as cs

logger = logging.getLogger(__name__)

new_password_generated_handler = Callable[[], None]


class AuthorizationBase(abc.ABC):
    """
    Base object for all authorization and authentication mechanisms, including symmetric-key
    and certificate-based auth.
    """

    def __init__(self) -> None:
        self.device_id: str = None
        self.module_id: str = None
        self.port: int = 8883
        self.api_version: str = constants.IOTHUB_V2_API_VERSION
        self.gateway_host_name: str = None
        self.hub_host_name: str = None
        self.content_type = constants.DEFAULT_CONTENT_TYPE
        self.dtmi = ""
        self.product_info = ""

    @property
    @abc.abstractmethod
    def password(self) -> str:
        pass

    @property
    def username(self) -> str:
        """
        Value to be sent in the MQTT `username` field.
        """
        props = {
            "h": self.hub_host_name,
            "did": self.device_id,
            "av": self.api_version,
        }

        if self.module_id:
            props["mid"] = self.module_id

        if self.dtmi:
            props["dtmi"] = self.dtmi

        if self.product_info:
            props["ca"] = self.product_info

        self.add_username_props(props)

        # TOOD: when we test this, we want to verify the characters in Max's spec
        return version_compat.urlencode(props)

    def add_username_props(self, props: Dict[str, Any]) -> None:
        pass

    @property
    def client_id(self) -> str:
        """
        Value to be sent in the MQTT `client_id` field.
        """
        if self.module_id:
            return "{}/{}".format(self.device_id, self.module_id)
        else:
            return self.device_id

    @property
    def hostname(self) -> str:
        if self.gateway_host_name:
            return self.gateway_host_name
        else:
            return self.hub_host_name


class RenewableTokenAuthorizationBase(AuthorizationBase):
    """
    Base class for authentication/authorization which uses a SAS token
    which needs to be refreshed on some periodic interval.  This base class does not
    specify _how_ the token gets refreshed, but it does control the interval that
    the token is valid and how frequently it needs to be refreshed.
    """

    def __init__(self) -> None:
        super(RenewableTokenAuthorizationBase, self).__init__()

        self.server_verification_cert: str = None
        self.password_renewal_timer: threading.Timer = None
        self.on_new_password_generated: new_password_generated_handler = None
        self.password_creation_time = 0
        self.password_expiry_time = 0
        self.shared_access_key_name = None
        self._password = None
        self.signing_mechanism: Any = None

    def add_username_props(self, props: Dict[str, Any]) -> None:
        props["am"] = "SAS"
        props["se"] = str(self.password_expiry_time * 1000)
        props["sa"] = str(self.password_creation_time * 1000)
        if self.shared_access_key_name:
            props["sp"] = self.shared_access_key_name

    @property
    def password(self) -> str:
        """
        Value to be sent in the MQTT `password` field.
        """
        return self._password

    @property
    def string_to_sign(self) -> str:
        """
        The string which is being signed to create the password
        """
        ss = "{host_name}\n{identity}\n{sas_policy}\n{sas_at}\n{sas_expiry}\n".format(
            host_name=self.hub_host_name,
            identity=self.client_id,
            sas_policy=self.shared_access_key_name or "",
            sas_at=self.password_creation_time * 1000,
            sas_expiry=self.password_expiry_time * 1000,
        )
        logger.info("String to sign=[{!r}]".format(ss.encode("ascii")))
        return ss

    @property
    def password_renewal_time(self) -> int:
        """
        The Unix epoch time when the password should be renewed.  This is typically
        some amount of time before the token expires.  That amount of time is known
        as the "token renewal margin"
        """
        return (
            self.password_expiry_time
            - constants.DEFAULT_PASSWORD_RENEWAL_MARGIN
        )

    @property
    def password_ready_to_renew(self) -> bool:
        """
        True if the current password is "ready to renew", meaning the current time is
        after the password's renewal time.
        """
        return time.time() > self.password_renewal_time

    @property
    def seconds_until_password_renewal(self) -> int:
        """
        Number of seconds before the current password needs to be removed.
        """
        return max(0, self.password_renewal_time - int(time.time()))

    def cancel_password_renewal_timer(self) -> None:
        """
        Cancel the running timer which is set to fire when the current password
        needs to be renewed.
        """
        if self.password_renewal_timer:
            self.password_renewal_timer.cancel()
            self.password_renewal_timer = None

    def set_password_renewal_timer(
        self, on_new_password_generated: new_password_generated_handler = None
    ) -> None:
        """
        Set a timer which renews the current password before it expires and calls
        the supplied handler after the renewal is complete.  The supplied handler
        is responsible for re-authorizing using the new password and setting up a new
        timer by calling `set_password_renewal_timer` again.

        :param function on_new_password_generated: Handler function which gets called after
            the password is renewed.  This function is responsible for calling
            `set_password_renewal_timer` in order to schedule subsequent renewals.
        """

        # If there is an old renewal timer, cancel it
        self.cancel_password_renewal_timer()
        self.on_new_password_generated = on_new_password_generated

        # Set a new timer.
        seconds_until_renewal = self.seconds_until_password_renewal
        self.password_renewal_timer = threading.Timer(
            seconds_until_renewal, self.renew_and_reconnect
        )
        self.password_renewal_timer.daemon = True
        self.password_renewal_timer.start()

        logger.info(
            "Password renewal timer set for {} seconds in the future, at approximately {}".format(
                seconds_until_renewal, self.password_expiry_time
            )
        )

    def _generate_new_password(self) -> None:
        self.password_creation_time = int(time.time())
        self.password_expiry_time = int(
            self.password_creation_time
            + constants.DEFAULT_PASSWORD_RENEWAL_INTERVAL
        )
        self._password = self.signing_mechanism.sign(self.string_to_sign)

    def renew_and_reconnect(self) -> None:
        """
        Renew authorization. This  causes a new password string to be generated and the
            `on_new_password_generated` function to be called.
        """
        logger.info("Renewing password and reconnecting")

        self.cancel_password_renewal_timer()

        self._generate_new_password()

        if self.on_new_password_generated:
            self.on_new_password_generated()

    def create_tls_context(self) -> ssl.SSLContext:
        """
        Create an SSLContext object based on this object.

        :returns: SSLContext object which can be used to secure the TLS connection.
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


class SymmetricKeyAuth(RenewableTokenAuthorizationBase):
    @classmethod
    def create_from_connection_string(cls, connection_string: str) -> Any:
        """
        create a new auth object from a connection string

        :param str connection_string: Connection string to create auth object for

        :returns: SymmetricKeyAuth object created by this function.
        """
        obj = SymmetricKeyAuth()
        obj._initialize(connection_string)
        return obj

    def _initialize(self, connection_string: str) -> None:
        """
        Helper function to initialize a newly created auth object.
        """
        conn_str = cs.ConnectionString(connection_string)

        self.hub_host_name = conn_str[cs.HOST_NAME]
        self.device_id = conn_str[cs.DEVICE_ID]
        self.module_id = conn_str.get(cs.MODULE_ID, None)
        self.gateway_host_name = conn_str.get(cs.GATEWAY_HOST_NAME, None)
        self.shared_access_key = conn_str[cs.SHARED_ACCESS_KEY]
        self.signing_mechanism = hmac_signing_mechanism.HmacSigningMechanism(
            self.shared_access_key
        )

        self._generate_new_password()
