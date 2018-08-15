import time

import machine
import ubinascii
from umqtt.robust import MQTTClient

import hass
from config import *

my_id = ubinascii.hexlify(machine.unique_id()).decode()

hass_api = hass.API(HASS_HOST, api_password=HASS_PASSWORD, port=HASS_PORT)

mqtt_client = MQTTClient(client_id=my_id,
                         server=MQTT_HOST,
                         port=MQTT_PORT,
                         user=MQTT_USER,
                         password=MQTT_PASSWORD)


def main():
    while not hass_api.validate_api():
        print("[HASS] Connecting to the server")
        time.sleep_ms(500)
    print("Home assistant connected")

    if mqtt_client.connect(clean_session=False):
        print("[MQTT] connected without persistent session")
    else:
        print("[MQTT] connected with persistent session")

    print("hello")
