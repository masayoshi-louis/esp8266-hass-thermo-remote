from machine import I2C

from config import DISP_I2C_ADDR
from ssd1306 import SSD1306_I2C

instance = None


class View:
    def write_to(self, driver: SSD1306_I2C):
        pass


class Display:
    __slots__ = ['driver']

    def __init__(self, i2c: I2C):
        self.driver = SSD1306_I2C(i2c=i2c, addr=DISP_I2C_ADDR, width=128, height=64)
        self.driver.init_display()

    def render(self, view: View):
        print("[DISP] rendering", repr(view))
        self.driver.fill(0)
        view.write_to(self.driver)
        self.driver.show()


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)


class SysStatusView(View):
    __slots__ = []

    def write_to(self, driver: SSD1306_I2C):
        from sys_status import instance as sys_status
        if sys_status.boot:
            driver.text('Starting...', 0, 0)
            if sys_status.sensor:
                driver.text('Sensor OK', 0, 10)
            else:
                driver.text('Sensor checking', 0, 10)
            if sys_status.hass_api:
                driver.text('HASS   OK', 0, 20)
            else:
                driver.text('HASS connecting', 0, 20)
            if sys_status.mqtt:
                driver.text('MQTT   OK', 0, 30)
            else:
                driver.text('MQTT connecting', 0, 30)
        else:
            driver.text('Running', 0, 0)
            driver.text('Sensor {}'.format('OK' if sys_status.sensor else 'fail'), 0, 10)
            driver.text('HASS   {}'.format('OK' if sys_status.hass_api else 'conn lost'), 0, 20)
            driver.text('MQTT   {}'.format('OK' if sys_status.mqtt else 'conn lost'), 0, 30)


sys_status_view = SysStatusView()
