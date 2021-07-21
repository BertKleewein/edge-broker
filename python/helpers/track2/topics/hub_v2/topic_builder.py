# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from uuid import uuid4
from typing import List, Tuple
from datetime import datetime
import six.moves.urllib as urllib
from . import topic_parser
from ...message import Message
from ... import version_compat

default_device_id = None
default_module_id = None


def set_default_identity(device_id: str, module_id: str = None) -> None:
    global default_device_id
    global default_module_id

    default_device_id = device_id
    default_module_id = module_id


def build_iothub_topic_prefix(
    device_id: str = None, module_id: str = None
) -> str:
    device_id = device_id or default_device_id
    module_id = module_id or default_module_id

    if device_id == default_device_id and module_id == default_module_id:
        return "$az/iot/"
    else:
        raise ValueError("topics for non-default identity not yet implemented")


def build_twin_get_response_subscribe_topic(
    device_id: str = None,
    module_id: str = None,
    include_wildcard_suffix: bool = True,
) -> str:
    topic = (
        build_iothub_topic_prefix(device_id, module_id) + "twin/get/response/"
    )
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_twin_patch_reported_response_subscribe_topic(
    device_id: str = None,
    module_id: str = None,
    include_wildcard_suffix: bool = True,
) -> str:
    topic = (
        build_iothub_topic_prefix(device_id, module_id) + "twin/patch/response/"
    )
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_twin_patch_desired_subscribe_topic(
    device_id: str = None,
    module_id: str = None,
    include_wildcard_suffix: bool = True,
) -> str:
    topic = (
        build_iothub_topic_prefix(device_id, module_id)
        + "twin/events/desired-changed/"
    )
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_twin_patch_reported_publish_topic(
    device_id: str = None, module_id: str = None
) -> str:
    return (
        build_iothub_topic_prefix(device_id, module_id)
        + "twin/patch/reported/?rid="
        + str(uuid4())
    )


def build_twin_get_publish_topic(
    device_id: str = None, module_id: str = None
) -> str:
    return (
        build_iothub_topic_prefix(device_id, module_id)
        + "twin/get/?rid="
        + str(uuid4())
    )


def build_telemetry_publish_topic(
    device_id: str = None, module_id: str = None, message: Message = None
) -> str:
    device_id = device_id or default_device_id
    module_id = module_id or default_module_id

    topic = build_iothub_topic_prefix(device_id, module_id) + "telemetry/"

    if message:
        topic += encode_message_properties_for_topic(message)

    return topic


def build_c2d_subscribe_topic(
    device_id: str = None,
    module_id: str = None,
    include_wildcard_suffix: bool = True,
) -> str:
    device_id = device_id or default_device_id
    module_id = module_id or default_module_id

    topic = (
        build_iothub_topic_prefix(device_id, module_id)
        + "messages/devicebound/"
    )
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_method_request_subscribe_topic(
    include_wildcard_suffix: bool = True,
) -> str:
    topic = "$iothub/methods/POST/"

    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_method_response_publish_topic(
    request_topic: str, status_code: str
) -> str:
    request_id = topic_parser.extract_request_id(request_topic)

    return "$iothub/methods/res/{status}/?$rid={request_id}".format(
        status=urllib.parse.quote(str(status_code), safe=""),
        request_id=urllib.parse.quote(str(request_id), safe=""),
    )


def encode_message_properties_for_topic(message_to_send: Message) -> str:
    """
    uri-encode the system properties of a message as key-value pairs on the topic with defined keys.
    Additionally if the message has user defined properties, the property keys and values shall be
    uri-encoded and appended at the end of the above topic with the following convention:
    '<key>=<value>&<key2>=<value2>&<key3>=<value3>(...)'
    :param message_to_send: The message to send
    :param topic: The topic which has not been encoded yet. For a device it looks like
    "devices/<deviceId>/messages/events/" and for a module it looks like
    "devices/<deviceId>/modules/<moduleId>/messages/events/
    :return: The topic which has been uri-encoded
    """
    topic = ""

    system_properties: List[Tuple[str, str]] = []

    if message_to_send.output_name:
        system_properties.append(("$.on", str(message_to_send.output_name)))
    if message_to_send.message_id:
        system_properties.append(("$.mid", str(message_to_send.message_id)))

    if message_to_send.correlation_id:
        system_properties.append(("$.cid", str(message_to_send.correlation_id)))

    if message_to_send.user_id:
        system_properties.append(("$.uid", str(message_to_send.user_id)))

    if message_to_send.content_type:
        system_properties.append(("$.ct", str(message_to_send.content_type)))

    if message_to_send.content_encoding:
        system_properties.append(
            ("$.ce", str(message_to_send.content_encoding))
        )

    if message_to_send.iothub_interface_id:
        system_properties.append(
            ("$.ifid", str(message_to_send.iothub_interface_id))
        )

    expiry = None
    if isinstance(message_to_send.expiry_time_utc, str):
        expiry = message_to_send.expiry_time_utc
    elif isinstance(message_to_send.expiry_time_utc, datetime):
        expiry = message_to_send.expiry_time_utc.isoformat()

    if expiry:
        system_properties.append(("$.exp", expiry))

    system_properties_encoded = version_compat.urlencode(
        system_properties, quote_via=urllib.parse.quote
    )
    topic += system_properties_encoded

    if (
        message_to_send.custom_properties
        and len(message_to_send.custom_properties) > 0
    ):
        if system_properties and len(system_properties) > 0:
            topic += "&"

        # Convert the custom properties to a sorted list in order to ensure the
        # resulting ordering in the topic string is consistent across versions of Python.
        # Convert to the properties to strings for safety.
        custom_prop_seq = [
            (str(i[0]), str(i[1]))
            for i in list(message_to_send.custom_properties.items())
        ]
        custom_prop_seq.sort()

        # Validate that string conversion has not created duplicate keys
        keys = [i[0] for i in custom_prop_seq]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate keys in custom properties!")

        user_properties_encoded = version_compat.urlencode(
            custom_prop_seq, quote_via=urllib.parse.quote
        )
        topic += user_properties_encoded

    return topic
