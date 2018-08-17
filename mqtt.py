import gc
import json
import time

import machine
import ubinascii
from machine import Timer
from micropython import const
from umqtt.robust import MQTTClient

from config import *

gc.collect()

_client = None

_hb_tim = None

_hb_tim_id = const(1)


def init():
    global _client
    global _hb_tim
    _client = MQTTClient(client_id=ubinascii.hexlify(machine.unique_id()).decode(),
                         server=MQTT_HOST,
                         port=MQTT_PORT,
                         user=MQTT_USER,
                         password=MQTT_PASSWORD,
                         keepalive=MQTT_KEEPALIVE)
    _client.set_last_will(_status_topic(), b'0', retain=True)
    while 1:
        try:
            if _client.connect(clean_session=False):
                print("[MQTT] Connected with persistent session")
            else:
                print("[MQTT] Connected without persistent session")
            _publish_birth_msg()
            _hb_tim = Timer(_hb_tim_id)
            _hb_tim.init(period=MQTT_HEARTBEAT_INTERVAL * 1000, mode=Timer.PERIODIC, callback=_heartbeat)
            break
        except OSError:
            print("[MQTT] Connecting...")
            time.sleep_ms(500)


def loop():
    while 1:
        _client.wait_msg()


def _status_topic():
    return '{}/{}'.format(HOSTNAME, 'status')


def _publish_birth_msg():
    print("[MQTT] Publishing birth message")
    _client.publish(_status_topic(), b'1', retain=True)


def _heartbeat(_timer):
    _publish_birth_msg()


def _hass_register_device(domain: str, sub_id: str, data):
    topic = '{}/{}/{}_{}/config'.format(HASS_MQTT_DISCOVERY_PREFIX, domain, HOSTNAME, sub_id)
    data_str = json.dumps(data)
    print("[MQTT] Publishing device config for {}/{}".format(domain, sub_id))
    print("[MQTT]   topic:", topic)
    print("[MQTT]   data:", data_str)
    _client.publish(topic, data_str.encode(), retain=True)


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
        config['availability_topic'] = _status_topic()
        config["payload_available"] = "1"
        config["payload_not_available"] = "0"
        _hass_register_device(self.domain, self.sub_id, config)

    def register(self, config):
        raise NotImplementedError


class HassMQTTSensor(HassMQTTDevice):
    __slots__ = ['mapper']

    def __init__(self, sub_id: str, mapper):
        super().__init__('sensor', sub_id)
        self.mapper = mapper

    def report_state(self, value):
        _client.publish(self.state_topic(), str(value).encode(), retain=True)

    def on_next(self, x):
        self.report_state(self.mapper(x))

    def register(self, config):
        self._register(config, enable_state=True, enable_command=False)


class HassMQTTTemperatureSensor(HassMQTTSensor):

    def __init__(self, sub_id: str = 'temperature', **kw):
        super().__init__(sub_id, **kw)

    def register(self, config):
        config['device_class'] = 'temperature'
        config['unit_of_measurement'] = TEMPERATURE_UNIT
        super().register(config)


class HassMQTTHumiditySensor(HassMQTTSensor):

    def __init__(self, sub_id: str = 'humidity', **kw):
        super().__init__(sub_id, **kw)

    def register(self, config):
        config['device_class'] = 'humidity'
        config['unit_of_measurement'] = '%'
        super().register(config)
