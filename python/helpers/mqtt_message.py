# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.


class MQTTMessage(object):
    def __init__(self) -> None:
        self.payload: bytes = None
        self.topic: str = None
