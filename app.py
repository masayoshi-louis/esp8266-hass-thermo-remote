import time

import hass
import mqtt
from config import *

hass_api = hass.API(HASS_HOST, api_password=HASS_PASSWORD, port=HASS_PORT)


def main():
    while not hass_api.validate_api():
        print("[HASS] Connecting to the server")
        time.sleep_ms(500)
    print("[HASS] Connected")

    mqtt.init()
