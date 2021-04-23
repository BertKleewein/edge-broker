# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import threading
from typing import Dict, Callable, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")
match_predicate = Callable[[ValueType], bool]


class WaitableDict(Generic[KeyType, ValueType]):
    def __init__(self) -> None:
        self.cv = threading.Condition()
        self.lookup: Dict[KeyType, ValueType] = {}

    def add_item(self, key: KeyType, value: ValueType) -> None:
        with self.cv:
            self.lookup[key] = value
            self.cv.notify_all()

    def get_next_item(self, key: KeyType, timeout: float) -> ValueType:
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
