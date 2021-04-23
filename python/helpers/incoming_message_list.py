# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import logging
from typing import List, Callable
import threading
from .mqtt_message import MQTTMessage
from . import topic_matcher

logger = logging.getLogger(__name__)

message_match_predicate = Callable[[str], bool]


class IncomingMessageList(object):
    def __init__(self) -> None:
        self.messages: List[MQTTMessage] = []
        self.cv = threading.Condition()

    def add_item(self, message: MQTTMessage) -> None:
        with self.cv:
            self.messages.append(message)
            self.cv.notify_all()

    def _pop_next(self, predicate: message_match_predicate) -> MQTTMessage:
        with self.cv:
            for message in self.messages:
                if predicate(message.topic):
                    self.messages.remove(message)
                    return message
        return None

    def _wait_and_pop_next(
        self, predicate: message_match_predicate, timeout: float
    ) -> MQTTMessage:
        with self.cv:
            return self.cv.wait_for(
                lambda: self._pop_next(predicate), timeout=timeout
            )

    def wait_for_message(self, timeout: float) -> bool:
        with self.cv:
            return self.cv.wait_for(
                lambda: len(self.messages) > 0, timeout=timeout
            )

    def pop_next_message(self, timeout: float) -> MQTTMessage:
        return self._wait_and_pop_next(lambda message: True, timeout=timeout)

    def pop_next_twin_patch_desired(self, timeout: float) -> MQTTMessage:
        return self._wait_and_pop_next(
            lambda message: topic_matcher.is_twin_patch_desired(message),
            timeout=timeout,
        )

    def pop_next_twin_response(
        self, request_topic: str, timeout: float
    ) -> MQTTMessage:
        return self._wait_and_pop_next(
            lambda message: topic_matcher.is_twin_response(
                message, request_topic
            ),
            timeout=timeout,
        )

    def pop_next_c2d(self, timeout: float) -> MQTTMessage:
        return self._wait_and_pop_next(
            lambda message: topic_matcher.is_c2d(message), timeout=timeout
        )

    def pop_next_method_request(
        self, timeout: float, method_name: str = None
    ) -> MQTTMessage:
        return self._wait_and_pop_next(
            lambda message: topic_matcher.is_method_request(
                message, method_name
            ),
            timeout=timeout,
        )
