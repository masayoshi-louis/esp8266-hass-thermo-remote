import utime as time
from dht import DHT22
from machine import Pin

import hass
import model
import mqtt
from config import *
from hass import ThermostatAPI as HassThermostatAPI
from thingflow import Scheduler


def main():
    hass_api = hass.API(HASS_BASE_URL, api_password=HASS_PASSWORD)
    hass_thermo = HassThermostatAPI(hass_api, HASS_THERMOSTAT_ID)
    sched = Scheduler()

    cur_state = hass_thermo.get_state()
    while cur_state is None:
        print("[HASS] Connecting to the server...")
        time.sleep_ms(500)
        cur_state = hass_thermo.get_state()
    print("[HASS] Connected")

    model.init(cur_state)

    # test
    # hass_thermo.set_heat_mode()
    # hass_thermo.set_temperature(30)

    mqtt.init(sched)

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x[0])
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x[1])
    h_sensor_mqtt.register({})

    dht_sensor = DHTSensor(Pin(PIN_DHT))

    sched.schedule_sensor(dht_sensor, 10, t_sensor_mqtt, h_sensor_mqtt)

    sched.run_forever()


class DHTSensor:
    __slots__ = ['s']

    def __init__(self, p):
        self.s = DHT22(p)

    def sample(self):
        self.s.measure()
        return [self.s.temperature(), self.s.humidity()]
