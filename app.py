import utime as time
from dht import DHT11
from machine import Pin, Timer
from micropython import const, schedule

import hass
import model
import mqtt
from config import *
from hass import ThermostatAPI as HassThermostatAPI

dht_sensor = None

DHT_TIM_ID = const(1)
dht_tim = None


def main():
    global dht_sensor
    global dht_tim

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

    dht_sensor = DHTSensor(PIN_DHT)

    dht_tim = Timer(DHT_TIM_ID)
    dht_tim.init(period=10000, mode=Timer.PERIODIC,
                 callback=_dht_updater(t_sensor_mqtt, h_sensor_mqtt, DHT2Model()))

    mqtt.loop()


class DHTSensor:
    __slots__ = ['dht', 'availability']

    def __init__(self, p):
        self.dht = DHT11(Pin(p))
        self.availability = True

    def sample(self):
        try:
            self.dht.measure()
            result = (self.dht.temperature(), self.dht.humidity())
            self.availability = True
            print("[DHT] T = {} {}, H = {} %".format(result[0], TEMPERATURE_UNIT, result[1]))
            return result
        except OSError as e:
            print("[DHT]", repr(e))
            self.availability = False
            return None


class DHT2Model:
    def on_next(self, x):
        model.instance.set_current_humidity(x[1])


def _dht_updater(*conns):
    def f(_timer):
        schedule(dht_push_sample, conns)

    return f


def dht_push_sample(conns):
    result = dht_sensor.sample()
    if result is not None:
        for s in conns:
            s.on_next(result)
