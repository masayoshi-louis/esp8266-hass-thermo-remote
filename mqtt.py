import machine
import ubinascii
from umqtt.robust import MQTTClient

from config import *

client = MQTTClient(client_id=ubinascii.hexlify(machine.unique_id()).decode(),
                    server=MQTT_HOST,
                    port=MQTT_PORT,
                    user=MQTT_USER,
                    password=MQTT_PASSWORD)

STATUS_TOPIC = ""


def init():

    if client.connect(clean_session=False):
        print("[MQTT] Connected without persistent session")
    else:
        print("[MQTT] Connected with persistent session")
