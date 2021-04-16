# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""This module contains a class representing messages that are sent or received.
"""
import json
from typing import Any, Union, Dict, List


class Message(object):
    """Represents a message to or from IoTHub
    """

    def __init__(
        self, data: Union[bytes, str, Dict[str, Any], List[Any]]
    ) -> None:
        """
        Initializer for Message

        :param data: The  data that constitutes the payload
        """
        self.data = data
        self.properties: Dict[str, str] = {}
        # TODO: set content_type and content_encoding based on type(data).  Do this in data setter so data can be changed and doesn't get converted to bytes until get_binary_payload is called.
        # TODO: properties and their encoding should be based on Max's yaml.

    @property
    def iothub_interface_id(self) -> str:
        assert False

    def set_as_security_message(self) -> None:
        """
        Set the message as a security message.

        This is a provisional API. Functionality not yet guaranteed.
        """
        assert False

    def get_binary_payload(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, str):
            return self.data.encode("utf-8")
        elif isinstance(self.data, dict):
            return json.dumps(self.data).encode("utf-8")
        elif isinstance(self.data, list):
            # TODO serialize array
            assert False
        else:
            assert False
