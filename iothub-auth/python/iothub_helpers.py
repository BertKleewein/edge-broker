# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
from typing import Dict
import uuid

logger = logging.getLogger(__name__)

RID = "rid"


def twin_get_publish_topic() -> str:
    return add_properties("$az/iot/twin/get/", {RID: str(uuid.uuid4())})


def twin_get_response_topic_filter() -> str:
    return "$az/iot/twin/get/response/#"


def is_twin_get_response_topic(topic: str, request_topic: str = None) -> bool:
    if not topic.startswith("$az/iot/twin/get/response/"):
        return False
    elif not request_topic:
        return True
    else:
        return does_rid_match(topic, request_topic)


def does_rid_match(topic: str, request_topic: str) -> bool:
    request_props = extract_properties(request_topic)
    response_props = extract_properties(topic)
    return (
        RID in request_props
        and RID in response_props
        and request_props[RID] == response_props[RID]
    )


def twin_patch_reported_publish_topic() -> str:
    return add_properties(
        "$az/iot/twin/patch/reported/", {RID: str(uuid.uuid4())}
    )


def twin_patch_reported_response_topic_filter() -> str:
    return "$az/iot/twin/patch/response/#"


def is_twin_patch_response_topic(topic: str, request_topic: str = None) -> bool:
    if not topic.startswith("$az/iot/twin/patch/response/"):
        return False
    elif not request_topic:
        return True
    else:
        return does_rid_match(topic, request_topic)


def twin_patch_desired_topic_filter() -> str:
    return "$az/iot/twin/events/desired/changed/#"


def send_message_publish_topic() -> str:
    return "$az/iot/telemetry"


def c2d_topic_filter() -> str:
    return "$az/iot/commands/#"


def method_request_topic_filter() -> str:
    # TODO
    pass


def get_method_name(request_topic: str) -> str:
    # TODO
    pass


def method_response_publish_topic(request_topic: str) -> str:
    # TODO
    pass


def add_properties(publish_topic: str, properties: Dict[str, str]) -> str:
    if "?" in publish_topic:
        props_to_add = extract_properties(publish_topic)
        publish_topic = publish_topic.split("?")[0]
    else:
        props_to_add = {}

    if not publish_topic.endswith("/"):
        publish_topic += "/"

    props_to_add.update(properties)

    return (
        publish_topic
        + "?"
        + "&".join(["{}={}".format(k, v) for (k, v) in props_to_add.items()])
    )


def extract_properties(topic: str) -> Dict[str, str]:
    parts = topic.split("?")
    if len(parts) < 2:
        return {}
    if len(parts) > 2:
        raise ValueError("Malformed topic: too many '?' characters")

    props = parts[1].split("&")
    # TODO: percent-un-encode
    return dict(arg[1].split("=", 1) for arg in props)  # type: ignore
