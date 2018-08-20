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
        print("[DISP] rendering", repr(view))
        self.driver.init_display()
        if isinstance(view, BootView):
            from sys_status import instance as sys_status
            if sys_status.boot:
                self.driver.text('Starting...', 0, 0)
                if sys_status.sensor:
                    self.driver.text('Sensor OK', 0, 10)
                else:
                    self.driver.text('Sensor checking', 0, 10)
                if sys_status.hass_api:
                    self.driver.text('HASS OK', 0, 20)
                else:
                    self.driver.text('HASS connecting', 0, 20)
                if sys_status.mqtt:
                    self.driver.text('MQTT OK', 0, 30)
                else:
                    self.driver.text('MQTT connecting', 0, 30)
            else:
                self.driver.text('Running', 0, 0)
                self.driver.text('Sensor {}'.format('OK' if sys_status.sensor else 'fail'), 0, 10)
                self.driver.text('HASS {}'.format('OK' if sys_status.hass_api else 'fail'), 0, 20)
                self.driver.text('MQTT {}'.format('OK' if sys_status.mqtt else 'fail'), 0, 30)
            self.driver.show()


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)


class BootView(View):
    pass
