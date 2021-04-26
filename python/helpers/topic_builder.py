# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from uuid import uuid4
from typing import Dict
import six.moves.urllib as urllib
from . import topic_parser, constants


def build_edge_topic_prefix(device_id: str, module_id: str) -> str:
    """
    Helper function to build the prefix that is common to all topics.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if build a prefix for a device.

    :return: The topic prefix, including the trailing slash (`/`)
    """
    if module_id:
        return "$iothub/{}/{}/".format(device_id, module_id)
    else:
        return "$iothub/{}/".format(device_id)


def build_iothub_topic_prefix(device_id: str, module_id: str = None) -> str:
    """
    return the string that is at the beginning of all topics for this
    device/module

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if build a prefix for a device.

    :return: The topic prefix, including the trailing slash (`/`)
    """

    # NOTE: Neither Device ID nor Module ID should be URL encoded in a topic string.
    # See the repo wiki article for details:
    # https://github.com/Azure/azure-iot-sdk-python/wiki/URL-Encoding-(MQTT)
    topic = "devices/" + str(device_id) + "/"
    if module_id:
        topic = topic + "modules/" + str(module_id) + "/"
    return topic


def build_twin_response_subscribe_topic(
    device_id: str, module_id: str = None, include_wildcard_suffix: bool = True
) -> str:
    """
    Build a topic string that can be used to subscribe to twin resopnses.  These
    are messages that are sent back from the service when the cilent sends a twin
    "get" operation or a twin "patch reported properties" operation.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if subscribing for a device.
    :param bool include_wildcard_suffix: True to include "#" at the end (for subscribing),
        False to exclude it (for topic matching)

    :return: The topic used when subscribing for twin resoponse messages.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        topic = build_edge_topic_prefix(device_id, module_id) + "twin/res/"
    else:
        topic = "$iothub/twin/res/"
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_twin_patch_desired_subscribe_topic(
    device_id: str, module_id: str, include_wildcard_suffix: bool = True
) -> str:
    """
    Build a topic string that can be used to subscribe to twin desired property
    patches for sepcified device or module.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if subscribing for a device.
    :param bool include_wildcard_suffix: True to include "#" at the end (for subscribing),
        False to exclude it (for topic matching)

    :return: The topic string used to subscribe to twin desired property patches.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        topic = build_edge_topic_prefix(device_id, module_id) + "twin/desired/"
    else:
        topic = "$iothub/twin/PATCH/properties/desired/"
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_twin_patch_reported_publish_topic(
    device_id: str, module_id: str
) -> str:
    """
    Build a topic string that can be used to publish a twin reported property patch.  This is a
    "one time" topic which can only be used once since it contains a unique identifier that is used
    to match request and response messages.

    The payload of the message should be a JSON object containing the twin's reported properties.
    This object should _not_ include the top level `"properties": { "reported": { ` wrapper
    objects that you see when viewing the entire device twin.

    The response to this `patch` operation is returned in a twin response message with a matching
    `request_id` value.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if publishing for a device.


    :return: The topic string used when publishing a reported properties patch to the service.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        return (
            build_edge_topic_prefix(device_id, module_id)
            + "twin/reported/?$rid="
            + str(uuid4())
        )
    else:
        return "$iothub/twin/PATCH/properties/reported/?$rid=" + str(uuid4())


def build_twin_get_publish_topic(device_id: str, module_id: str) -> str:
    """
    Build a topic string that can be used to get a device twin from the service.  This is a
    "one time" topic which can only be used once since it contains a unique identifier that is used.

    The payload of this message should be left empty.

    The response to this `get` operation is returned in a twin response message with a matching
    `request_id` value.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if publishing for a device.

    :return: The topic string used publish a twin get operation to the service.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        return (
            build_edge_topic_prefix(device_id, module_id)
            + "twin/get/?$rid="
            + str(uuid4())
        )
    else:
        return "$iothub/twin/GET/?$rid=" + str(uuid4())


def build_telemetry_publish_topic(
    device_id: str, module_id: str, properties: Dict[str, str] = None
) -> str:
    """
    Build a topic string that can be used to publish device/module telemetry to the service.  If
    a properties array is provided, those properties are encoded into the topic string.  This topic
    _can_ be reused if publishing for the same device/module with the same properties.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if publishing for a device.

    :return: The topic string used publish device/module telemetry to the service.
    """
    assert not properties
    # TODO: properties

    if constants.EDGEHUB_TOPIC_RULES:
        return (
            build_edge_topic_prefix(device_id, module_id) + "messages/events/"
        )
    else:
        return (
            build_iothub_topic_prefix(device_id, module_id) + "messages/events/"
        )


def build_c2d_subscribe_topic(
    device_id: str, module_id: str, include_wildcard_suffix: bool = True
) -> str:
    """
    Build a topic string that can be used to subscribe to C2D messages for the device or module.

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module.  Set to `None` if subscribing for a device.
    :param bool include_wildcard_suffix: True to include "#" at the end (for subscribing),
        False to exclude it (for topic matching)

    :return: The topic string used subscribe to C2D messages.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        topic = (
            build_edge_topic_prefix(device_id, module_id) + "messages/c2d/post/"
        )
    else:
        topic = (
            build_iothub_topic_prefix(device_id, module_id)
            + "messages/devicebound/"
        )
    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_method_request_subscribe_topic(
    device_id: str, module_id: str, include_wildcard_suffix: bool = True
) -> str:
    """
    Build a topic string that can be used to subscribe to method requests

    :param str device_id: The device_id for the device or module.
    :param str module_id: (optional) The module_id for the module. Set to `None` if subscribing for a device.
    :param bool include_wildcard_suffix: True to include "#" at the end (for subscribing),
        False to exclude it (for topic matching)

    :return: The topic string used to subscribe to method requests.
    """
    if constants.EDGEHUB_TOPIC_RULES:
        topic = build_edge_topic_prefix(device_id, module_id) + "methods/post/"
    else:
        topic = "$iothub/methods/POST/"

    if include_wildcard_suffix:
        return topic + "#"
    else:
        return topic


def build_method_response_publish_topic(
    request_topic: str, status_code: str
) -> str:
    """
    Build a topic string that can be used to publish a resopnse to a specific method request.  This
    topic is built based on a specific method request, so it can only be used once, in response to
    that specific request.

    :param str request_topic: The topic from the method request message that is being responded to.
    :param str status code: The result code for the method response.

    :return: The topic string used to return method results to the service.
    """
    request_id = topic_parser.extract_request_id(request_topic)

    if constants.EDGEHUB_TOPIC_RULES:
        device_id = topic_parser.extract_device_id(request_topic)
        module_id = topic_parser.extract_module_id(request_topic)

        return build_edge_topic_prefix(
            device_id, module_id
        ) + "methods/res/{}/?$rid={}".format(
            urllib.parse.quote(str(status_code), safe=""),
            urllib.parse.quote(str(request_id), safe=""),
        )
    else:
        return "$iothub/methods/res/{status}/?$rid={request_id}".format(
            status=urllib.parse.quote(str(status_code), safe=""),
            request_id=urllib.parse.quote(str(request_id), safe=""),
        )
