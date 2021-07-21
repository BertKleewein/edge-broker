# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import os
import sys
import logging
from sample_base import SampleAppBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


class SampleApp(SampleAppBase):
    def __init__(self) -> None:
        super(SampleAppBase, self).__init__()

    def main(self) -> None:
        self.init(os.environ["IOTHUB_CONNECTION_STRING"])

        print("Connecting")
        self.start_connect()

        if self.connection_status.wait_for_connected(timeout=20):
            print("failed to connect.  exiting")
            sys.exit(1)


if __name__ == "__main__":
    SampleApp().main()
