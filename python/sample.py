import json
import logging
import os
import threading
import paho
from helpers import topics, mqtt_edge_auth
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from typing import Any

# A map of sensors' MAC to device id.
# All devices need to be pre-created in IoT Hub.

authorized_devices = json.loads(os.environ["AUTHORIZED_DEVICES"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleApp(object):
    def __init__(self) -> None:
        self._mqtt_client: paho.mqtt.client.Client = None
        self._topic_helper: topics.IoTHubTopicHelper = None
        self._connected = threading.Event()

    def handle_on_connect(self, userdata: Any, flags: Any, rc: int) -> None:
        logger.info("handle_on_connect called with rc={}".format(rc))
        if rc == 0:
            self._connected.set()

    def main(self) -> None:
        logger.info("Azure IoT Edge Protocol Translation Module (PTM) Sample")

        auth = mqtt_edge_auth.MqttEdgeAuth.create_from_environment()

        self._topic_helper = topics.IoTHubTopicHelper(
            auth.device_id, auth.module_id
        )

        self._mqtt_client = paho.mqtt.client.Client(auth.client_id)
        self._mqtt_client.username_pw_set(auth.username, auth.password)
        self._mqtt_client.tls_set_context(auth.tls_context)
        self._mqtt_client.on_connect = self.handle_on_connect

        logger.info("Connecting")
        self._mqtt_client.connect(auth.hostname, auth.port)

        if not self._connected.wait(timeout=20):
            logger.error("Failed to connect.")

        else:
            logger.info("listening for sensors data.")
            RuuviTagSensor.get_datas(
                self.sensor_callback, list(authorized_devices.keys())
            )

        logger.info("Exiting.")

    # This is a callback that gets called when we get data from the Ruuvi library
    def sensor_callback(self, data: Any) -> None:
        mac = data[0]
        payload = data[1]

        # Get the device_id from the mac address of the sensor
        device_id = authorized_devices.get(mac, None)

        # Get the telemetry topic for this device
        topic = self._topic_helper.get_telemetry_topic_for_publish(device_id)

        # publish
        info = self._mqtt_client.publish(
            topic, json.dumps(payload), qos=1, userdata=device_id
        )
        if info.rc:
            logger.info(
                "sending telemetry to {} failed with error: '{}'".format(
                    device_id, paho.mqtt.client.error_string(info.rc)
                )
            )

        else:
            logger.info(
                "sent telemetry to {} with MID {}".format(device_id, info.mid)
            )

    def handle_on_publish(self, userdata: Any, mid: int) -> None:
        # callback for publish comlplete.
        logger.info(
            "PUBACK received for telemetry sent to {} with MID {}".format(
                userdata, mid
            )
        )


if __name__ == "__main__":
    SampleApp().main()
