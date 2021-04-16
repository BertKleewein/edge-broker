# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
from typing import Union, Any, Dict, Callable
from uuid import uuid4

TopicFilter = Union[str, Callable[[str], bool]]
IncomingMessageHandler = Callable[[str, object], None]
TopicProperties = Dict[str, str]
CompletionCallback = Callable[[Exception, Union[Any, None]], None]

use_default_value: str = str(uuid4())
match_any_value: str = str(uuid4())


class BaseTopicHelper(object):
    def __init__(
        self, default_device_id: str = None, default_module_id: str = None
    ):
        """
        Create a topic helper, with an optional default identity.

        if default_module_id == None, that means our default is a device with no module
        if default_device_id == None, that means we don't have a default.
        Calling APIs to build/parse topics without a module_id assumes it's a device
        Calling APIs to build/parse topics without a device_id causes an exception if the
            device_id is required.
        """
        if (
            default_device_id == use_default_value
            or default_device_id == match_any_value
        ):
            raise ValueError(
                "device_id cannot be use_default_value or match_any_value"
            )
        if (
            default_module_id == use_default_value
            or default_module_id == match_any_value
        ):
            raise ValueError(
                "module_id cannot be use_default_value or match_any_value"
            )
        if default_module_id and not default_device_id:
            raise ValueError(
                "if module_id is specified, device_id must be specified"
            )

        self.default_device_id = default_device_id
        self.default_module_id = default_module_id

    def get_device_id_to_use_for_publish(self, device_id: str) -> str:
        """
        Get device_id used for publishing.  If one is provided, use it.  If not,
        use the default.  Either way, device_id is required.
        """
        id_to_use = device_id
        if id_to_use == use_default_value:
            id_to_use = self.default_device_id

        if not id_to_use:
            raise ValueError("device_id or default_device_id must be specified")
        return id_to_use

    def get_module_id_to_use_for_publish(self, module_id: str) -> str:
        """
        Get module_id used for publishing.  If one is provided, use it.  If not,
        use the default.  module_id is not required
        """
        id_to_use = module_id
        if id_to_use == use_default_value:
            id_to_use = self.default_module_id

        return id_to_use

    def _get_topic_base(self, device_id: str, module_id: str = None) -> str:
        """
        return the string that is at the beginning of all topics for this
        device/module
        """
        # TODO: rewrite for new API
        # TODO: copy comments from mqtt_topic_iothub.py as appropriate

        # NOTE: Neither Device ID nor Module ID should be URL encoded in a topic string.
        # See the repo wiki article for details:
        # https://github.com/Azure/azure-iot-sdk-python/wiki/URL-Encoding-(MQTT)
        device_id = self.get_device_id_to_use_for_publish(device_id)
        module_id = self.get_module_id_to_use_for_publish(module_id)

        topic = "devices/" + str(device_id)
        if module_id:
            topic = topic + "/modules/" + str(module_id)
        return topic

    # Generic extraction routines
    def extract_request_id(self, topic: str) -> str:
        """
        Extract the $rid from the topic.
        Raises an ValueError if there is no $rid in the topic
        """
        assert False

    def extract_device_id(self, topic: str) -> str:
        """
        Extract the device_id from the topic.
        Raises an ValueError if there is no device_id in the topic
        """
        assert False

    def extract_module_id(self, topic: str) -> str:
        """
        Extract the module_id from the topic.
        Raises an ValueError if there is no module_id in the topic
        """
        assert False

    def extract_properties(self, topic: str) -> TopicProperties:
        """
        Extract the properties from the topic.
        returns {} if there are no properties in the topic
        """
        assert False

    def is_topic_for_device(
        self, topic: str, device_id: str = use_default_value
    ) -> bool:
        """
        returns True if the given topic is intended for the given device
        """
        assert False

    def is_topic_for_module(
        self,
        topic: str,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
    ) -> bool:
        """
        returns True if the givern topic is indended for the given device/module
        """
        assert False

    pass


class TelemetryTopicHelper(BaseTopicHelper):
    # Telemetry
    def get_telemetry_topic_for_publish(
        self,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
        properties: TopicProperties = None,
    ) -> str:
        """
        Return the telemetry topic to publish to.

        When publishing, we can specify device_id/module_id or we can use the defaults.
        """
        # TODO: add properties to topic
        assert not properties
        return self._get_topic_base(device_id, module_id) + "/messages/events/"


class C2dTopicHelper(BaseTopicHelper):
    # C2D
    def get_c2d_topic_for_subscribe(
        self,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
    ) -> str:
        """
        Return the topic we need to subscribe to for C2d.

        For subscribes, we always subscribe for all devices/modules
        """
        # TODO: do we always subscribe for all devices/modules

        return (
            self._get_topic_base(device_id, module_id)
            + "/messages/devicebound/#"
        )

    def is_c2d_topic(
        self,
        topic: str,
        device_id: str = match_any_value,
        module_id: str = match_any_value,
    ) -> bool:
        """
        Return True if the given topic is C2D.
        If device_id and module_id == use_default_value, it only returns True if the C2D is targeted
            at the default.
        If device_id and module_id == match_any_value, it returns True if the C2D is targeted at
            any destinations.
        """
        # TODO: write topic_matches function
        return topic.startswith(
            self._get_topic_base(device_id, module_id)
            + "/messages/devicebound/"
        )


class TwinTopicHelper(BaseTopicHelper):
    # Twin
    def get_twin_response_topic_for_subscribe(self) -> str:
        """
        Return the topic that we need to subscribe to for twin responses
        """
        assert False

    def get_twin_patch_desired_topic_for_subscribe(self) -> str:
        """
        Return the topic that we need to subscribe to for twin desired property patches
        """
        assert False

    def is_twin_response_topic(
        self,
        device_id: str = match_any_value,
        module_id: str = match_any_value,
        request_id: str = match_any_value,
        request_topic: str = match_any_value,
    ) -> bool:
        """
        Return True if the given topic is a twin response for the given parameters.
        Return False if the given topic does not match the parameters.
        Return False if the given topic is not a twin response topic.
        If no parameters are specified, return True if the given topic is a twin response.
        """
        assert False

    def is_twin_patch_topic(
        self, device_id: str = match_any_value, module_id: str = match_any_value
    ) -> bool:
        """
        return True if the given topic is a twin patch topic
        """
        assert False

    def get_twin_onetime_request_topic_for_publish(
        self,
        verb: str,
        resource: str,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
        properties: TopicProperties = None,
    ) -> str:
        """
        Getm a publish topic for a twin operation, specifying verb and resource.
        This is a onetime topic because it contains an $rid value and can only be used for one twin operation
        """
        assert False

    def get_twin_onetime_fetch_topic_for_publish(
        self,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
        properties: TopicProperties = None,
    ) -> str:
        """
        Get a publish topic for a twin 'get' operation.
        This is a onetime topic because it contains an $rid value and can only be used for one twin operation
        """
        assert False

    def get_twin_onetime_patch_reported_topic_for_publish(
        self,
        device_id: str = use_default_value,
        module_id: str = use_default_value,
    ) -> str:
        """
        Get a publish topic for a twin 'patch' operation.
        This is a onetime topic because it contains an $rid value and can only be used for one twin operation
        """


class MethodTopicHelper(BaseTopicHelper):
    def extract_method_name(self, topic: str) -> str:
        """
        Extract the method_name from the topic.
        Raises an ValueError if there is no method_name in the topic
        """
        assert False

    # Methods
    def get_method_received_topic_for_subscribe(self) -> str:
        """
        return the topic we need to subscribe to for method requests
        """
        assert False

    def is_method_request_topic(
        self,
        device_id: str = match_any_value,
        module_id: str = match_any_value,
        method_name: str = match_any_value,
    ) -> bool:
        """
        Return true if the given topic isa  method request for the given parameters
        """
        assert False

    def get_method_response_topic_for_publish(
        self, request_topic: str, result_code: str
    ) -> str:
        """
        Return a method response topic for the given method request topic and result code.
        """
        assert False


class IoTHubTopicHelper(BaseTopicHelper):
    def __init__(
        self, default_device_id: str = None, default_module_id: str = None
    ):
        super(IoTHubTopicHelper, self).__init__(
            default_device_id, default_module_id
        )
        self.telemetry = TelemetryTopicHelper(
            default_device_id, default_module_id
        )
        self.c2d = C2dTopicHelper(default_device_id, default_module_id)
        self.twin = TwinTopicHelper(default_device_id, default_module_id)
        self.methods = MethodTopicHelper(default_device_id, default_module_id)
