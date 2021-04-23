# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from typing import Dict
import six.moves.urllib as urllib


def extract_request_id(topic: str) -> str:
    return extract_properties(topic)["rid"]


def extract_device_id(topic: str) -> str:
    pass


def extract_module_id(topic: str) -> str:
    pass


def extract_properties(topic: str) -> Dict[str, str]:
    """Return a dictionary of properties from a string in the format
    ${key1}={value1}&${key2}={value2}...&${keyn}={valuen}
    """
    # TODO: this will be re-written with new topic rules
    properties = topic.split("?")[1]
    d = {}
    kv_pairs = properties.split("&")

    for entry in kv_pairs:
        pair = entry.split("=")
        key = urllib.parse.unquote(pair[0]).lstrip("$")
        value = urllib.parse.unquote(pair[1])
        d[key] = value

    return d
