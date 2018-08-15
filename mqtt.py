import machine
import ubinascii
from umqtt.robust import MQTTClient

from config import *

client = MQTTClient(client_id=ubinascii.hexlify(machine.unique_id()).decode(),
                    server=MQTT_HOST,
                    port=MQTT_PORT,
                    user=MQTT_USER,
                    password=MQTT_PASSWORD,
                    keepalive=60)

STATUS_TOPIC = '{}/{}'.format(HOSTNAME, 'status')


def init():
    client.set_last_will(STATUS_TOPIC, b'0', retain=True)
    if client.connect(clean_session=False):
        print("[MQTT] Connected with persistent session")
    else:
        print("[MQTT] Connected without persistent session")
    client.publish(STATUS_TOPIC, b'1', retain=True)
