import utime as time
from dht import DHT11
from machine import Pin, Timer
from micropython import const

import hass
import model
import mqtt
from config import *
from hass import ThermostatAPI as HassThermostatAPI

_dht_sensor = None

_dht_tim_id = const(2)
_dht_tim = None


def main():
    global _dht_sensor
    global _dht_tim

    hass_api = hass.API(HASS_BASE_URL, api_password=HASS_PASSWORD)
    hass_thermo = HassThermostatAPI(hass_api, HASS_THERMOSTAT_ID)

    cur_state = hass_thermo.get_state()
    while cur_state is None:
        print("[HASS] Connecting to the server...")
        time.sleep_ms(500)
        cur_state = hass_thermo.get_state()
    print("[HASS] Connected")

    # max_temp = cur_state.attributes.max_temp
    # min_temp = cur_state.attributes.min_temp

    model.init(cur_state)

    # test
    # hass_thermo.set_heat_mode()
    # hass_thermo.set_temperature(30)

    mqtt.init()

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x[0])
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x[1])
    h_sensor_mqtt.register({})

    _dht_sensor = DHTSensor(PIN_DHT)

    _dht_tim = Timer(_dht_tim_id)
    _dht_tim.init(period=10000, mode=Timer.PERIODIC,
                  callback=_dht_updater(t_sensor_mqtt, h_sensor_mqtt, DHT2Model()))

    mqtt.loop()


class DHTSensor:
    __slots__ = ['s', 'sensor_id']

    def __init__(self, p):
        self.s = DHT11(Pin(p))
        self.sensor_id = 'DHT'

    def sample(self):
        while 1:
            try:
                self.s.measure()
                result = [self.s.temperature(), self.s.humidity()]
                print("[DHT] T = {} {}, H = {} %".format(result[0], TEMPERATURE_UNIT, result[1]))
                return result
            except OSError as e:
                print("[DHT]", repr(e), "retry")


class DHT2Model:
    def on_next(self, x):
        model.instance.set_current_humidity(x[1])


def _dht_updater(*conns):
    def f(_timer):
        result = _dht_sensor.sample()
        for s in conns:
            s.on_next(result)

    return f
