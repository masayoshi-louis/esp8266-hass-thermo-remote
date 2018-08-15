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
        print("Connecting to the home assistant server")

    if not mqtt_client.connect(clean_session=False):
        print("WARN: MQTT server does not support persistent session")

    print("hello")
