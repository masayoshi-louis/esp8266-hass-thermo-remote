import machine
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

sys_status = None

dht_sensor = None

DHT_TIM_ID = const(1)
dht_tim = None


def main():
    global sys_status
    global dht_sensor
    global dht_tim

    sys_status = SystemStatus()

    dht_sensor = DHTSensor(PIN_DHT)
    while 1:
        try:
            dht_sensor.sample()  # test sensor
            sys_status.set_sensor(True)
            break
        except OSError as e:
            print("Sensor failure", repr(e))
            time.sleep(3)

    hass_api = hass.API(HASS_BASE_URL, api_password=HASS_PASSWORD)
    hass_thermo = HassThermostatAPI(hass_api, HASS_THERMOSTAT_ID)

    cur_state = hass_thermo.get_state()
    while cur_state is None:
        print("[HASS] Connecting to the server...")
        time.sleep_ms(500)
        cur_state = hass_thermo.get_state()
    print("[HASS] Connected")
    sys_status.set_hass_api(True)

    # max_temp = cur_state.attributes.max_temp
    # min_temp = cur_state.attributes.min_temp

    model.init(cur_state)

    # test
    # hass_thermo.set_heat_mode()
    # hass_thermo.set_temperature(30)

    mqtt.init(mqtt_msg_dispatch)
    sys_status.set_mqtt(True)

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x.t)
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x.h)
    h_sensor_mqtt.register({})

    dht_tim = Timer(DHT_TIM_ID)
    sensor_update = dht_updater(t_sensor_mqtt, h_sensor_mqtt, DHT2Model())
    sensor_update(None)
    dht_tim.init(period=SENSOR_SAMPLE_INTERVAL * 1000, mode=Timer.PERIODIC,
                 callback=sensor_update)

    while 1:
        mqtt.loop()


class DHTSensor:
    __slots__ = ['dht', 'prev_sample']

    def __init__(self, p):
        self.dht = DHT11(Pin(p))
        self.prev_sample = SensorSample(-1000, -1000, -1000)

    def sample(self):
        self.dht.measure()
        result = SensorSample(self.dht.temperature(), self.dht.humidity(), -1000)
        self.prev_sample = result
        print("[DHT] T = {} {}, H = {} % RH".format(result.t, TEMPERATURE_UNIT, result.h))
        return result


class DHT2Model:
    def on_next(self, x: SensorSample):
        model.instance.set_current_temperature(float(x.t))


def dht_updater(*conns):
    def f(_timer):
        schedule(dht_push_sample, conns)

    return f


def dht_push_sample(conns):
    try:
        result = dht_sensor.sample()
    except OSError as e:
        print("[DHT]", repr(e))
        sys_status.set_sensor(False)
        machine.reset()
        result = None  # actually impossible
    if result is not None:
        for s in conns:
            s.on_next(result)


class SystemStatus:
    __slots__ = ['sensor', 'hass_api', 'mqtt']

    def __init__(self):
        self.sensor = False
        self.hass_api = False
        self.mqtt = False
        self.__update_led()

    def set_sensor(self, v: bool):
        self.sensor = v
        self.__on_update("Sensor", v)

    def set_hass_api(self, v: bool):
        self.hass_api = v
        self.__on_update("Home assistant API", v)

    def set_mqtt(self, v: bool):
        self.mqtt = v
        self.__on_update("MQTT client", v)

    def __on_update(self, item: str, v: bool):
        print("{} is{} OK".format(item, '' if v else ' not'))
        self.__update_led()

    def __update_led(self):
        led = Pin(2, Pin.OUT)
        s = self.sensor and self.hass_api and self.mqtt
        led.value(s)


def mqtt_msg_dispatch(topic, msg):
    model.instance.update_by_mqtt(topic.decode(), msg.decode())
