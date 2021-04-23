# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from . import topic_parser


def is_twin_response(topic: str, request_topic: str) -> bool:
    if topic.startswith("$iothub/twin/res/"):
        return topic_parser.extract_request_id(
            topic
        ) == topic_parser.extract_request_id(request_topic)
    else:
        return False


def is_twin_patch_desired(topic: str) -> bool:
    return topic.startswith("$iothub/twin/PATCH/properties/desired/")


def is_c2d(topic: str) -> bool:
    return "/messages/devicebound/" in topic


def is_method_request(topic: str, method_name: str = None) -> bool:
    prefix = "$iothub/methods/POST/"
    if method_name:
        prefix += method_name + "/"
    return topic.startswith(prefix)
