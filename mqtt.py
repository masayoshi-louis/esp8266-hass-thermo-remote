import time

import json
import machine
import ubinascii
from umqtt.robust import MQTTClient

from config import *

client = MQTTClient(client_id=ubinascii.hexlify(machine.unique_id()).decode(),
                    server=MQTT_HOST,
                    port=MQTT_PORT,
                    user=MQTT_USER,
                    password=MQTT_PASSWORD,
                    keepalive=MQTT_KEEPALIVE)

STATUS_TOPIC = '{}/{}'.format(HOSTNAME, 'status')


def init():
    client.set_last_will(STATUS_TOPIC, b'0', retain=True)
    while 1:
        try:
            if client.connect(clean_session=False):
                print("[MQTT] Connected with persistent session")
            else:
                print("[MQTT] Connected without persistent session")
            client.publish(STATUS_TOPIC, b'1', retain=True)
            break
        except OSError:
            print("[MQTT] Connecting...")
            time.sleep_ms(500)


def _hass_register_device(domain: str, sub_id: str, data):
    topic = '{}/{}/{}_{}/config'.format(HASS_MQTT_DISCOVERY_PREFIX, domain, HOSTNAME, sub_id)
    data_str = json.dumps(data)
    print("[MQTT] Publishing device config for {}/{}".format(domain, sub_id))
    print("[MQTT]   topic:", topic)
    print("[MQTT]   data:", data_str)
    client.publish(topic, data_str.encode(), retain=True)


class HassMQTTDevice:
    __slots__ = ['domain', 'sub_id']

    def __init__(self, domain: str, sub_id: str):
        self.domain = domain
        self.sub_id = sub_id

    def entity_id(self):
        return "{}/{}/{}".format(HOSTNAME, self.domain, self.sub_id)

    def state_topic(self):
        return self.entity_id()

    def command_topic(self):
        return "{}/set".format(self.entity_id())

    def _register(self, config, enable_state=True, enable_command=False):
        config['name'] = '{}_{}'.format(HOSTNAME, self.sub_id)
        config['platform'] = 'mqtt'
        if enable_state:
            config['state_topic'] = self.state_topic()
        if enable_command:
            config['command_topic'] = self.command_topic()
        config['availability_topic'] = STATUS_TOPIC
        config["payload_available"] = "1"
        config["payload_not_available"] = "0"
        _hass_register_device(self.domain, self.sub_id, config)

    def register(self, config):
        raise NotImplementedError


class HassMQTTSensor(HassMQTTDevice):

    def __init__(self, sub_id: str):
        super().__init__('sensor', sub_id)

    def report_state(self, value):
        client.publish(self.state_topic(), str(value).encode(), retain=True)

    def register(self, config):
        self._register(config, enable_state=True, enable_command=False)


class HassMQTTTemperatureSensor(HassMQTTSensor):

    def __init__(self, sub_id: str = 'temperature'):
        super().__init__(sub_id)

    def register(self, config):
        config['device_class'] = 'temperature'
        config['unit_of_measurement'] = TEMPERATURE_UNIT
        super().register(config)


class HassMQTTHumiditySensor(HassMQTTSensor):

    def __init__(self, sub_id: str = 'humidity'):
        super().__init__(sub_id)

    def register(self, config):
        config['device_class'] = 'humidity'
        config['unit_of_measurement'] = '%'
        super().register(config)
