# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import base64
import json
import logging
import urllib

import requests
import requests_unixsocket

requests_unixsocket.monkeypatch()
logger = logging.getLogger(__name__)


class EdgeWorkloadApi:
    """
    Constructor for instantiating a iot hsm object.  This is an object that
    communicates with the Azure IoT Edge HSM in order to get connection credentials
    for an Azure IoT Edge module.  The credentials that this object return come in
    two forms:

    1. The trust bundle, which is a certificate that can be used as a trusted cert
       to authenticate the SSL connection between the IoE Edge module and IoT Edge
    2. A signing function, which can be used to create the sig field for a
       SharedAccessSignature string which can be used to authenticate with Iot Edge
    """

    def __init__(
        self,
        module_id: str,
        generation_id: str,
        workload_uri: str,
        api_version: str,
    ):
        """
        Constructor for instantiating a Azure IoT Edge HSM object

        :param str module_id: The module id
        :param str api_version: The API version
        :param str generation_id: The module generation id
        :param str workload_uri: The workload uri
        """
        self.module_id = urllib.parse.quote(module_id, safe="")  # type: ignore
        self.api_version = api_version
        self.generation_id = generation_id
        self.workload_uri = _format_socket_uri(workload_uri)

    def get_certificate(self) -> str:
        """
        Return the server verification certificate from the trust bundle that can be used to
        validate the server-side SSL TLS connection that we use to talk to Edge

        :return: The server verification certificate to use for connections to the Azure IoT Edge
        instance, as a PEM certificate in string form.

        :raises: IoTEdgeError if unable to retrieve the certificate.
        """
        r = requests.get(
            self.workload_uri + "trust-bundle",
            params={"api-version": self.api_version},
        )
        # Validate that the request was successful
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise OSError("Unable to get trust bundle from Edge") from e
        # Decode the trust bundle
        try:
            bundle = r.json()
        except ValueError as e:
            raise OSError("Unable to decode trust bundle") from e
        # Retrieve the certificate
        try:
            cert = bundle["certificate"]
        except KeyError as e:
            raise OSError("No certificate in trust bundle") from e
        return cert  # type: ignore

    def sign(self, data_str: str) -> str:
        """
        Use the IoTEdge HSM to sign a piece of string data.  The caller should then insert the
        returned value (the signature) into the 'sig' field of a SharedAccessSignature string.

        :param str data_str: The data string to sign

        :return: The signature, as a URI-encoded and base64-encoded value that is ready to
        directly insert into the SharedAccessSignature string.

        :raises: IoTEdgeError if unable to sign the data.
        """
        encoded_data_str = base64.b64encode(data_str.encode("utf-8")).decode()

        path = "{workload_uri}modules/{module_id}/genid/{gen_id}/sign".format(
            workload_uri=self.workload_uri,
            module_id=self.module_id,
            gen_id=self.generation_id,
        )
        sign_request = {
            "keyId": "primary",
            "algo": "HMACSHA256",
            "data": encoded_data_str,
        }

        r = requests.post(  # can we use json field instead of data?
            url=path,
            params={"api-version": self.api_version},
            data=json.dumps(sign_request),
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise OSError("Unable to sign data") from e
        try:
            sign_response = r.json()
        except ValueError as e:
            raise OSError("Unable to decode signed data") from e
        try:
            signed_data_str: str = sign_response["digest"]
        except KeyError as e:
            raise OSError("No signed data received") from e

        return signed_data_str


def _format_socket_uri(old_uri: str) -> str:
    """
    This function takes a socket URI in one form and converts it into another form.

    The source form is based on what we receive inside the IOTEDGE_WORKLOADURI
    environment variable, and it looks like this:
    "unix:///var/run/iotedge/workload.sock"

    The destination form is based on what the requests_unixsocket library expects
    and it looks like this:
    "http+unix://%2Fvar%2Frun%2Fiotedge%2Fworkload.sock/"

    The function changes the prefix, uri-encodes the path, and adds a slash
    at the end.

    If the socket URI does not start with unix:// this function only adds
    a slash at the end.

    :param old_uri: The URI in IOTEDGE_WORKLOADURI form

    :return: The URI in requests_unixsocket form
    """
    old_prefix = "unix://"
    new_prefix = "http+unix://"
    new_uri: str = None

    if old_uri.startswith(old_prefix):
        stripped_uri = old_uri[len(old_prefix) :]
        if stripped_uri.endswith("/"):
            stripped_uri = stripped_uri[:-1]
        new_uri = new_prefix + urllib.parse.quote(  # type: ignore
            stripped_uri, safe=""
        )
    else:
        new_uri = old_uri

    if not new_uri.endswith("/"):
        new_uri += "/"

    return new_uri
