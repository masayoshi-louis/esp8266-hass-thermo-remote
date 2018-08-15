import hass
import mqtt
from config import *
from thingflow import Scheduler

hass_api = None
sched = None


def main():
    global hass_api
    global sched
    hass_api = hass.API(HASS_BASE_URL, api_password=HASS_PASSWORD)
    sched = Scheduler()

    # while not hass_api.validate_api():
    #     print("[HASS] Connecting to the server...")
    #     time.sleep_ms(500)
    # print("[HASS] Connected")

    mqtt.init(sched)

    # test
    sensor = mqtt.HassMQTTTemperatureSensor()
    sensor.register({})
    sensor.report_state(25.5)

    sched.run_forever()
