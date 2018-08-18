import utime as time
from dht import DHT11
from machine import Pin, Timer
from micropython import const, schedule

import hass
import model
import mqtt
from config import *
from hass import ThermostatAPI as HassThermostatAPI
from model import SensorSample

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

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x.t)
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x.h)
    h_sensor_mqtt.register({})

    dht_sensor = DHTSensor(PIN_DHT)

    dht_tim = Timer(DHT_TIM_ID)
    sensor_update = dht_updater(t_sensor_mqtt, h_sensor_mqtt, DHT2Model())
    sensor_update(None)
    dht_tim.init(period=SENSOR_SAMPLE_INTERVAL * 1000, mode=Timer.PERIODIC,
                 callback=sensor_update)

    mqtt.loop()


class DHTSensor:
    __slots__ = ['dht', 'availability', 'prev_sample']

    def __init__(self, p):
        self.dht = DHT11(Pin(p))
        self.availability = True
        self.prev_sample = SensorSample(-1000, -1000, -1000)

    def sample(self):
        try:
            self.dht.measure()
            result = SensorSample(self.dht.temperature(), self.dht.humidity(), -1000)
            self.prev_sample = result
            self.availability = True
            print("[DHT] T = {} {}, H = {} % RH".format(result.t, TEMPERATURE_UNIT, result.h))
            return result
        except OSError as e:
            print("[DHT]", repr(e))
            self.availability = False
            return None


class DHT2Model:
    def on_next(self, x: SensorSample):
        model.instance.set_current_humidity(x.h)


def dht_updater(*conns):
    def f(_timer):
        schedule(dht_push_sample, conns)

    return f


def dht_push_sample(conns):
    result = dht_sensor.sample()
    if result is not None:
        for s in conns:
            s.on_next(result)
