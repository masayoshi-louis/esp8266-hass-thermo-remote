import gc
import json

import machine
import ubinascii
import utime as time
from umqtt import simple

from config import *

gc.collect()

_client = None


class MQTTClient(simple.MQTTClient):
    DELAY = 2
    DEBUG = True

    __slots__ = ['pending_msg', 'reconnect_listeners', 'disconnect_listeners']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pending_msg = {}
        self.reconnect_listeners = [self.publish_pending_msgs]
        self.disconnect_listeners = []

    def on_reconnect(self, l):
        self.reconnect_listeners.append(l)

    def on_disconnected(self, l):
        self.disconnect_listeners.append(l)

    def __fire_disconnected(self):
        for notify in self.disconnect_listeners:
            notify()

    def delay(self, _i):
        time.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        i = 0
        while 1:
            try:
                r = super().connect(False)
                for notify in self.reconnect_listeners:
                    notify()
                return r
            except OSError as e:
                self.log(True, e)
                i += 1
                self.delay(i)

    def publish_pending_msgs(self):
        d = self.pending_msg.copy()
        self.pending_msg.clear()
        for key, value in d.items():
            self.publish(key, value[0], value[1], value[2])

    def publish(self, topic, msg, retain=False, qos=0):
        try:
            return super().publish(topic, msg, retain, qos)
        except OSError as e:
            self.log(False, e)
            self.pending_msg[topic] = (msg, retain, qos)
            self.__fire_disconnected()

    def wait_msg(self):
        while 1:
            try:
                return super().wait_msg()
            except OSError as e:
                self.log(False, e)
                self.__fire_disconnected()
            self.reconnect()


def init(status_listener):
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
            status_listener(True)
            _client.on_reconnect(_publish_birth_msg)
            _client.on_reconnect(lambda: status_listener(True))
            _client.on_disconnected(lambda: status_listener(False))
            break
        except OSError:
            print("[MQTT] Connecting...")
            time.sleep_ms(500)


def loop():
    _client.check_msg()


def _status_topic():
    return '{}/{}'.format(HOSTNAME, 'status')


def _publish_birth_msg():
    print("[MQTT] Publishing birth message")
    _client.publish(_status_topic(), b'1', retain=True)


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
