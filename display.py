from machine import I2C

from config import DISP_I2C_ADDR
from ssd1306 import SSD1306_I2C
from writer import Writer

from font import freesans23, freesans40
from model import LocalChanges

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


class NormalView(View):
    __slots__ = []

    def write_to(self, driver: SSD1306_I2C):
        from model import instance as model
        from model import OP_MODE_OFF, STATE_HEAT

        is_heating = (model.state == STATE_HEAT)

        wri_t = Writer(driver, freesans40, verbose=False)
        wri_t.set_clip(False, False, False)  # Char wrap
        Writer.set_textpos(driver, 16, 26)
        if is_heating:
            driver.fill_rect(0, 14, driver.width, wri_t.height(), 1)
        wri_t.printstring(str(int(model.current_temperature)) + ".", invert=is_heating)

        wri_t_s = Writer(driver, freesans23, verbose=False)
        wri_t_s.set_clip(False, False, False)  # Char wrap
        Writer.set_textpos(driver, 29, 82)
        wri_t_s.printstring(str(model.current_temperature)[-1:], invert=is_heating)

        if is_heating:
            driver.fill_rect(0, 52, driver.width, 4, 0)

        driver.text("{0:.1f}%RH".format(model.sensor_sample.h), 0, 0)
        pressure_str = "{0:.1f}kPa".format(model.sensor_sample.p / 10)
        driver.text(pressure_str, driver.width - len(pressure_str) * 8, 0)
        driver.text("room", driver.height - 16, 56)
        if model.operation_mode == OP_MODE_OFF:
            driver.text("OFF", driver.width - 24, 20)


class SettingView(View):
    __slots__ = ['lc']

    def __init__(self, local_changes: LocalChanges):
        self.lc = local_changes

    def write_to(self, driver: SSD1306_I2C):
        from model import ATTR_OP_MODE

        driver.text("set", driver.height - 12, 56)

        wri = Writer(driver, freesans40, verbose=False)
        if self.lc.last_item == ATTR_OP_MODE:
            text = self.lc.operation_mode.upper()
            text_w = wri.stringlen(text)
            Writer.set_textpos(driver, 16, int((driver.width - text_w) / 2))
            wri.printstring(text)
        else:
            Writer.set_textpos(driver, 16, 26)
            wri.printstring("{0:.1f}".format(self.lc.temperature))
