import esp
import utime as time
from machine import I2C
from machine import Pin, Timer
from micropython import const, schedule

import hass
import model
import mqtt
from bme280 import BME280
from config import *
from controller import Controller
from display import BootView
from display import init as init_display
from display import instance as display
from hass import ThermostatAPI as HassThermostatAPI
from model import SensorSample, LocalChanges
from sys_status import instance as sys_status

dht_sensor = None

DHT_TIM_ID = const(1)
dht_tim = None


def main():
    global dht_sensor
    global dht_tim

    i2c = I2C(scl=Pin(PIN_I2C_SCL), sda=Pin(PIN_I2C_SDA))
    init_display(i2c)

    display.render(BootView())

    dht_sensor = DHTSensor(PIN_DHT)
    while 1:
        try:
            dht_sensor.sample()  # test sensor
            sys_status.set_sensor(True)
            display.render(BootView())
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
    display.render(BootView())

    model.init(cur_state)

    mqtt.init(mqtt_msg_dispatch)
    sys_status.set_mqtt(True)
    display.render(BootView())
    time.sleep(1)
    sys_status.boot = False

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x.t)
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x.h)
    h_sensor_mqtt.register({})

    dht_tim = Timer(DHT_TIM_ID)
    sensor_update = dht_updater(t_sensor_mqtt, h_sensor_mqtt, DHT2Model())
    sensor_update(None)
    dht_tim.init(period=SENSOR_SAMPLE_INTERVAL * 1000, mode=Timer.PERIODIC,
                 callback=sensor_update)

    controller = Controller(hass_thermo_api=hass_thermo,
                            local_changes=LocalChanges(max_temp=float(cur_state.attributes.max_temp),
                                                       min_temp=float(cur_state.attributes.min_temp)))

    if LIGHT_SLEEP_ENABLED:
        esp.sleep_type(esp.SLEEP_LIGHT)

    while 1:
        mqtt.loop()
        controller.loop()


class DHTSensor:
    __slots__ = ['driver', 'prev_sample']

    def __init__(self, i2c):
        self.driver = BME280(i2c=i2c, address=SENSOR_I2C_ADDR)
        self.prev_sample = SensorSample(-1000, -1000, -1000)

    def sample(self):
        result = self.driver.sample()
        self.prev_sample = result
        print("[DHT] T = {} {}, H = {} % RH".format(result.t, TEMPERATURE_UNIT, result.h))
        return result


class DHT2Model:
    def on_next(self, x: SensorSample):
        model.instance.update_sensor_sample(x)


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
        result = None  # actually impossible
    if result is not None:
        for s in conns:
            s.on_next(result)


def mqtt_msg_dispatch(topic, msg):
    model.instance.update_by_mqtt(topic.decode(), msg.decode())
