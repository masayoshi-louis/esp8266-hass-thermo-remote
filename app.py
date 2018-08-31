import esp
import machine
import utime as time
from dht import DHT22
from machine import I2C
from machine import Pin, Timer
from micropython import const, schedule

import hass
import model
import mqtt
from bme280 import BME280
from config import *
from controller import Controller
from display import init as init_display
from display import sys_status_view
from hass import ThermostatAPI as HassThermostatAPI
from model import SensorSample, LocalChanges
from sht31 import SHT31
from sys_status import instance as sys_status

from tsl2561 import TSL2561

dht_sensor = None

DHT_TIM_ID = const(1)
dht_tim = None

# battery voltage
V_TIM_ID = const(2)
v_tim = None
v_adc = machine.ADC(0)

last_light_sensor_sample_ts = 0
current_display_brightness = 255

LIGHT_SENSOR_SAMPLE_INTERVAL = const(1000)


def main():
    global dht_sensor
    global dht_tim
    global v_tim

    try:
        i2c = I2C(scl=Pin(PIN_I2C_SCL), sda=Pin(PIN_I2C_SDA))
        init_display(i2c)
    except OSError as e:
        print("Can not initialize display!", repr(e))
        time.sleep(10)
        machine.reset()
        return

    from display import instance as display
    display.render(sys_status_view)

    while 1:
        try:
            dht_sensor = MultiSensor(pin=PIN_DHT, i2c=i2c)
            dht_sensor.sample()  # test sensor
            sys_status.set_sensor(True)
            display.render(sys_status_view)
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
    display.render(sys_status_view)

    model.init(cur_state)

    mqtt.init(mqtt_msg_dispatch)
    sys_status.set_mqtt(True)
    display.render(sys_status_view)
    time.sleep(1)
    sys_status.boot = False
    display.render(sys_status_view)

    t_sensor_mqtt = mqtt.HassMQTTTemperatureSensor(mapper=lambda x: x.t)
    t_sensor_mqtt.register({})

    h_sensor_mqtt = mqtt.HassMQTTHumiditySensor(mapper=lambda x: x.h)
    h_sensor_mqtt.register({})

    v_sensor_mqtt = mqtt.HassMQTTVoltageSensor()
    v_sensor_mqtt.register({})

    dht_tim = Timer(DHT_TIM_ID)
    sensor_update = dht_updater(t_sensor_mqtt, h_sensor_mqtt, Sensor2Model())
    sensor_update(None)
    dht_tim.init(period=SENSOR_SAMPLE_INTERVAL * 1000, mode=Timer.PERIODIC,
                 callback=sensor_update)

    v_tim = Timer(V_TIM_ID)
    v_update = voltage_updater(v_sensor_mqtt)
    v_update(None)
    v_tim.init(period=30 * 1000, mode=Timer.PERIODIC,
               callback=v_update)

    controller = Controller(hass_thermo_api=hass_thermo,
                            thermostat_model=model.instance,
                            local_changes=LocalChanges(max_temp=float(cur_state['attributes']['max_temp']),
                                                       min_temp=float(cur_state['attributes']['min_temp'])))

    if LIGHT_SLEEP_ENABLED:
        esp.sleep_type(esp.SLEEP_LIGHT)

    lux_sensor = TSL2561(i2c=i2c)
    lux_sensor.active(True)
    time.sleep_ms(500)

    while 1:
        adjust_display_brightness(lux_sensor)
        mqtt.loop()
        controller.loop()


class MultiSensor:
    __slots__ = ['dht', 'bme', 'sht', 'prev_sample']

    def __init__(self, pin: int, i2c: I2C):
        self.dht = DHT22(Pin(pin))
        self.bme = BME280(i2c=i2c, address=BME280_I2C_ADDR)
        self.sht = SHT31(i2c, addr=SHT31_I2C_ADDR)
        self.prev_sample = SensorSample(-1000, -1000, -1000)

    def sample(self):
        try:
            self.dht.measure()
            dht_result = SensorSample(self.dht.temperature(), self.dht.humidity(), -1000)
            print("[SENSOR] DHT22:  T = {} {}, H = {} % RH".format(dht_result.t, TEMPERATURE_UNIT, dht_result.h))
        except OSError as e:
            print("[SENSOR] DHT22 is not available")
            dht_result = None
            if SENSOR_MAIN == "dht":
                raise e

        try:
            _sht_result = self.sht.get_temp_humi()
            sht_result = SensorSample(round(_sht_result[0], 1), round(_sht_result[1], 1), -1000)
            print("[SENSOR] SHT31:  T = {} {}, H = {} % RH".format(sht_result.t, TEMPERATURE_UNIT, sht_result.h))
        except OSError as e:
            print("[SENSOR] SHT31 is not available")
            sht_result = None
            if SENSOR_MAIN == "sht":
                raise e

        try:
            bme_result = self.bme.sample()
            bme_result.t = round(bme_result.t, 1)
            bme_result.h = round(bme_result.h, 1)
            print(
                "[SENSOR] BME280: T = {} {}, H = {} % RH, P = {} hPa".format(bme_result.t, TEMPERATURE_UNIT,
                                                                             bme_result.h,
                                                                             bme_result.p))
        except OSError as e:
            print("[SENSOR] BME280 is not available")
            bme_result = None
            if SENSOR_MAIN == "bme":
                raise e

        if SENSOR_MAIN == "dht":
            result = dht_result
        if SENSOR_MAIN == "sht":
            result = sht_result
        if SENSOR_MAIN == "bme":
            result = bme_result

        if bme_result is not None:
            result.p = bme_result.p

        self.prev_sample = result
        return result


class Sensor2Model:
    def on_next(self, x: SensorSample):
        model.instance.update_sensor_sample(x)


def dht_updater(*conns):
    def f(_timer):
        schedule(sensor_push_sample, conns)

    return f


def sensor_push_sample(conns):
    try:
        result = dht_sensor.sample()
    except OSError as e:
        print("[SENSOR]", repr(e))
        sys_status.set_sensor(False)
        result = None  # actually impossible
    if result is not None:
        for s in conns:
            s.on_next(result)


def mqtt_msg_dispatch(topic, msg):
    model.instance.update_by_mqtt(topic.decode(), msg.decode())


def voltage_updater(sink):
    def f(_timer):
        schedule(push_voltage, sink)

    return f


def push_voltage(sink):
    raw = v_adc.read()
    v = raw / 1024 * 5
    print("[BATTERY] voltage = {0:.2f}v".format(v))
    sink.on_next(v)


def adjust_display_brightness(sensor: TSL2561):
    from display import instance as display
    global last_light_sensor_sample_ts
    global current_display_brightness
    now = time.ticks_ms()
    if now - last_light_sensor_sample_ts > LIGHT_SENSOR_SAMPLE_INTERVAL:
        lux = sensor.read()
        if lux >= 40:
            b = 255
        elif lux >= 20:
            b = 80
        else:
            b = int(lux)
        if abs(current_display_brightness - b) > 15 or (b <= 10 < current_display_brightness):
            current_display_brightness = b
            display.set_brightness(b)
            print("[LIGHT] {} lux, set display brightness to {}".format(lux, b))
        last_light_sensor_sample_ts = now
