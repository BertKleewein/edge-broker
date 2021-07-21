# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import threading


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
