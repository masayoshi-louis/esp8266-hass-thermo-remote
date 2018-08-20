from machine import I2C

from ssd1306 import SSD1306_I2C
from config import DISP_I2C_ADDR

instance = None


class View:
    pass


class Display:
    __slots__ = ['driver']

    def __init__(self, i2c: I2C):
        self.driver = SSD1306_I2C(i2c=i2c, addr=DISP_I2C_ADDR, width=128, height=64)

    def render(self, view: View):
        self.driver.init_display()
        if view is BootView:
            from sys_status import instance as sys_status
            if sys_status.boot:
                self.driver.text('Starting...', 0, 0)
            else:
                self.driver.text('Running', 0, 0)
            self.driver.text('Sensor is{} OK'.format('' if sys_status.sensor else ' not'), 0, 10)
            self.driver.text('HASS connection is{} OK'.format('' if sys_status.hass_api else ' not'), 0, 20)
            self.driver.text('MQTT connection is{} OK'.format('' if sys_status.mqtt else ' not'), 0, 30)


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)


class BootView(View):
    pass
