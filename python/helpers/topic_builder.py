# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from uuid import uuid4
from typing import Dict
import six.moves.urllib as urllib
from . import topic_parser


def build_twin_response_subscribe_topic(device_id: str, module_id: str) -> str:
    return "$iothub/twin/res/#"


def build_twin_patch_desired_subscribe_topic(
    device_id: str, module_id: str
) -> str:
    return "$iothub/twin/PATCH/properties/desired/#"


def build_twin_patch_reported_publish_topic(
    device_id: str, module_id: str
) -> str:
    return "$iothub/twin/{method}{resource_location}?$rid={request_id}".format(
        method="PATCH",
        resource_location="/properties/reported/",
        request_id=str(uuid4()),
    )


def build_twin_get_publish_topic(device_id: str, module_id: str) -> str:
    return "$iothub/twin/{method}{resource_location}?$rid={request_id}".format(
        method="GET", resource_location="/", request_id=str(uuid4())
    )


def build_telemetry_publish_topic(
    device_id: str, module_id: str, properties: Dict[str, str] = None
) -> str:
    assert not properties

    topic = "devices/" + str(device_id)
    if module_id:
        topic = topic + "/modules/" + str(module_id)

    return topic + "/messages/events/"


def build_c2d_subscribe_topic(device_id: str, module_id: str) -> str:
    topic = "devices/" + str(device_id)
    if module_id:
        topic = topic + "/modules/" + str(module_id)

    return topic + "/messages/devicebound/#"


def build_method_request_subscribe_topic(device_id: str, module_id: str) -> str:
    return "$iothub/methods/POST/#"


def build_method_response_publish_topic(
    request_topic: str, status_code: str
) -> str:
    request_id = topic_parser.extract_request_id(request_topic)
    return "$iothub/methods/res/{status_code}/?$rid={request_id}".format(
        status_code=urllib.parse.quote(str(status_code), safe=""),
        request_id=urllib.parse.quote(str(request_id), safe=""),
    )
