import utime as time

import hass
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

    # test
    # hass_thermo.set_heat_mode()
    # hass_thermo.set_temperature(30)

    mqtt.init(sched)

    # test
    sensor = mqtt.HassMQTTTemperatureSensor()
    sensor.register({})
    sensor.report_state(25.5)

    sched.run_forever()
