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
        self.driver.init_display()

    def render(self, view: View):
        pass


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)


class BootView(View):
    pass
