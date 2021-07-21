# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import threading
import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)


class IncomingAckList(object):
    """
    Dictionary-like object which supports the concept of "waiting" for a specific key to be
    set.  This way, code that needs to wait for a specific PUBACK or SUBACK to be returned
    can easily be written using `get_next_item` with a specific `key` value.

    These "wait" operations are done in a thread-safe manner using the `Condition` class
    provided by the `threading` module.

    Callers using `asyncio` instead of `threading` should consider writing an awaitable version
    of this class using the `asyncio.Condition` class for synchronization.  Submitting a pull
    request with this functionality is encouraged.
    """

    def __init__(self) -> None:
        self.cv = threading.Condition()
        self.lookup: Dict[int, Any] = {}

    def add_item(self, key: int, value: Any) -> None:
        """
        Add the ack to the dict and notify any waiting listeners
        """
        with self.cv:
            self.lookup[key] = value
            self.cv.notify_all()

    def wait_for_item(self, key: int, timeout: float) -> Any:
        """
        Wait for a given ack to be added to the dict.
        """

        def received() -> bool:
            return key in self.lookup

        with self.cv:
            if not self.cv.wait_for(received, timeout=timeout):
                return None
            else:
                try:
                    return self.lookup.pop(key)
                except KeyError:
                    # possible multiple readers.  Not really a big deal.
                    logger.error(
                        "{} was removed from lookup list between notification and retrieval.".format(
                            key
                        )
                    )
                    return None

    def was_received(self, key: int) -> bool:
        """
        return True if a given ack was received
        """
        with self.cv:
            return key in self.lookup


message_match_predicate = Callable[[str], bool]


class IncomingMessageList(object):
    """
    thread-safe object used to keep track of incoming MQTT messages.  This object
    supports the concept of "waiting" for specific types of messages to be added to the list.
    In this way, "do-work" loops can be written which wait for specific types of messages to
    arrive and functions can be written to wait for messages like twin responses with specific
    request_id values.

    These "wait" operations are done in a thread-safe manner using the `Condition` class
    provided by the `threading` module.

    Callers using `asyncio` instead of `threading` should consider writing an awaitable version
    of this class using the `asyncio.Condition` class for synchronization.  Submitting a pull
    request with this functionality is encouraged.
    """

    def __init__(self) -> None:
        self.messages: List[Any] = []
        self.cv = threading.Condition()

    def add_item(self, message: Any) -> None:
        """
        Add a message to the message list and notify any listeners which might be
        waiting for this message.

        :param object message: The incoming message.
        """
        with self.cv:
            self.messages.append(message)
            self.cv.notify_all()

    def _pop_next(self, predicate: message_match_predicate) -> Any:
        """
        Internal function to remove and return the next message in the list
        which satisfies the passed predicate.

        :param callable predicate: Function which accepts a message object and
            Returns True if that message satisfies some condition.  When this function
            returns True for some message, that message will be removed from the list and
            returned to the caller.

        :returns: The first message in our internal list which satisfies the internal predicate.
            `None` if our internal list is empty or if no messages match the predicate.
        """

        with self.cv:
            for message in self.messages:
                if predicate(message.topic):
                    self.messages.remove(message)
                    return message
        return None

    def _wait_and_pop_next(
        self, predicate: message_match_predicate, timeout: float
    ) -> Any:
        """
        Internal function which waits until a message which matches the given predicate
        gets added to our list.

        :param callable predicate: function which accepts a message object and returns
            True if that message can be returned from this function.
        :param float timeout: Amount of time to wait before returning.

        :returns: The objet which satisfies the predicate, or `None` if no matching object
            becomes available before the timeout elapses.
        """

        with self.cv:
            return self.cv.wait_for(
                lambda: self._pop_next(predicate),  # type: ignore
                timeout=timeout,
            )

    def wait_for_message(self, timeout: float) -> bool:
        """
        Wait for the list to be not-empty.  If the list already has a
        message, return `True` immediately.  If not, then wait up to `timeout`
        seconds for an item to be added, and then return `True`.  If no item
        is addeded within `timeout` seconds, return False.

        :param float timeout: Amount of time to wait before returning.

        :return: `True` if the list has an item, `False` otherwise.
        """
        with self.cv:
            return self.cv.wait_for(
                lambda: len(self.messages) > 0, timeout=timeout
            )

    def pop_next_message(self, timeout: float) -> Any:
        """
        Returns the next message in the list.  If no message is in the list,
        waits for up to `timeout` seconds for one to be added.

        :param float timeout: Amount of time to wait before returning.  `0` to
            check the list and return immediately without waiting.

        :returns: The next message in the list, or `None` if no message gets
            added before the timeout elapses.
        """
        return self._wait_and_pop_next(lambda message: True, timeout=timeout)


class ConnectionStatus(object):
    def __init__(self) -> None:
        self.cv = threading.Condition()
        self._connected = False
        self._disconnected_error: Exception = None

    @property
    def connected(self) -> bool:
        with self.cv:
            return self._connected

    @connected.setter
    def connected(self, connected: bool) -> None:
        with self.cv:
            self._error_state = None
            if self._connected != connected:
                self._connected = connected
                self.cv.notify_all()

    @property
    def disconnected_error(self) -> Exception:
        with self.cv:
            return self.disconnected_error

    @disconnected_error.setter
    def disconnected_error(self, disconnected_error: Exception) -> None:
        if not disconnected_error:
            raise ValueError(
                "disconnected_error must be truthy.  Set connected flag to clear disconnected_error property"
            )
        with self.cv:
            if self._connected or not self._disconnected_error:
                self._connected = False
                self._disconnected_error = disconnected_error
                self.cv.notify_all()

    def wait_for_connected(self, timeout: float = None) -> None:
        with self.cv:
            self.cv.wait_for(
                lambda: self._connected or self._disconnected_error,
                timeout=timeout,
            )
            if self._disconnected_error:
                raise self._disconnected_error

    def wait_for_disconnected(self, timeout: float = None) -> None:
        with self.cv:
            self.cv.wait_for(lambda: not self._connected, timeout=timeout)
