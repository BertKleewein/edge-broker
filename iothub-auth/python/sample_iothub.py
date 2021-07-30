# Copyright (c) Microsoft Corporation. All rights reserved.S
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import os
import sys
import logging
import argparse
from paho_client import PahoClient
import iothub_helpers

logger = logging.getLogger(__name__)

"""
Uncomment the following lines to enable debug logging
"""

logging.basicConfig(level=logging.INFO)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


class SampleApp(object):
    def __init__(self) -> None:
        pass

    def send_telemetry(self) -> None:
        """
        Demonstrates how to send iothub telemetry
        """
        client = PahoClient.create_from_connection_string(
            os.environ["IOTHUB_DEVICE_CONNECTION_STRING"]
        )

        print("Starting connection")
        client.start_connect()

        print("Waiting for CONNACK")
        if not client.connection_status.wait_for_connected(timeout=20):
            print("failed to connect.  exiting")
            sys.exit(1)

        print("Sending telemetry")
        topic = iothub_helpers.send_message_publish_topic()
        payload = {
            "latitude": 47.63962283908785,
            "longitude": -122.12718926895407,
        }
        (rc, mid) = client.publish(topic, str(payload), qos=1)

        print("Waiting for puback")
        client.incoming_pubacks.wait_for_ack(mid, timeout=20)

        print("Disconnecting")
        client.disconnect()
        client.connection_status.wait_for_disconnected()


samples = ["send_telemetry"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="sample")
    parser.add_argument(
        "sample", type=str, help="Sample to run", choices=list(samples)
    )

    args = parser.parse_args()

    app = SampleApp()
    sample_function = getattr(app, args.sample)
    sample_function()
