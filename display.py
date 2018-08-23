from machine import I2C
from micropython import const

from config import DISP_I2C_ADDR
from font import freesans23, freesans40
from model import LocalChanges
from sh1106 import SH1106_I2C
from writer import Writer

instance = None

ROW_OFFSET = const(0)

ROTATE = True


class View:
    def write_to(self, driver: SH1106_I2C):
        pass


class Display:
    __slots__ = ['driver']

    def __init__(self, i2c: I2C):
        self.driver = SH1106_I2C(i2c=i2c, addr=DISP_I2C_ADDR, width=128, height=64)
        if ROTATE:
            self.driver.rotate(True, update=True)

    def render(self, view: View):
        self.driver.fill(0)
        view.write_to(self.driver)
        self.driver.show()


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)


class SysStatusView(View):
    __slots__ = []

    def write_to(self, driver: SH1106_I2C):
        from sys_status import instance as sys_status
        if sys_status.boot:
            driver.text('Starting...', 0, ROW_OFFSET)
            if sys_status.sensor:
                driver.text('Sensor OK', 0, 10 + ROW_OFFSET)
            else:
                driver.text('Sensor checking', 0, 10 + ROW_OFFSET)
            if sys_status.hass_api:
                driver.text('HASS   OK', 0, 20)
            else:
                driver.text('HASS connecting', 0, 20 + ROW_OFFSET)
            if sys_status.mqtt:
                driver.text('MQTT   OK', 0, 30)
            else:
                driver.text('MQTT connecting', 0, 30 + ROW_OFFSET)
        else:
            driver.text('Running', 0, ROW_OFFSET)
            driver.text('Sensor {}'.format('OK' if sys_status.sensor else 'fail'), 0, 10 + ROW_OFFSET)
            driver.text('HASS   {}'.format('OK' if sys_status.hass_api else 'conn lost'), 0, 20 + ROW_OFFSET)
            driver.text('MQTT   {}'.format('OK' if sys_status.mqtt else 'conn lost'), 0, 30 + ROW_OFFSET)


sys_status_view = SysStatusView()


class NormalView(View):
    __slots__ = ['data']

    def __init__(self, data):
        self.data = data

    def write_to(self, driver: SH1106_I2C):
        from model import OP_MODE_OFF, STATE_HEAT

        is_heating = (self.data.state == STATE_HEAT)

        wri_t = Writer(driver, freesans40, verbose=False)
        wri_t.set_clip(False, False, False)  # Char wrap
        Writer.set_textpos(driver, 16 + ROW_OFFSET, 26)
        if is_heating:
            driver.fill_rect(0, 14 + ROW_OFFSET, driver.width - 10, wri_t.height(), 1)
        wri_t.printstring(str(int(self.data.current_temperature)) + ".", invert=is_heating)

        wri_t_s = Writer(driver, freesans23, verbose=False)
        wri_t_s.set_clip(False, False, False)  # Char wrap
        Writer.set_textpos(driver, 29 + ROW_OFFSET, 82)
        wri_t_s.printstring(str(self.data.current_temperature)[-1:], invert=is_heating)

        if is_heating:
            driver.fill_rect(0, 52 + ROW_OFFSET, driver.width, 4, 0)
            driver.text("H", driver.width - 8, 16 + ROW_OFFSET)
            driver.text("E", driver.width - 8, 16 + 9 + ROW_OFFSET)
            driver.text("A", driver.width - 8, 16 + 9 * 2 + ROW_OFFSET)
            driver.text("T", driver.width - 8, 16 + 9 * 3 + ROW_OFFSET)

        driver.text("{0:.1f}%RH".format(self.data.sensor_sample.h), 0, ROW_OFFSET)
        pressure_str = "{0:.1f}kPa".format(self.data.sensor_sample.p / 10)
        driver.text(pressure_str, driver.width - len(pressure_str) * 8, 0 + ROW_OFFSET)
        driver.text("room", driver.height - 16, 56 + ROW_OFFSET)
        if self.data.operation_mode == OP_MODE_OFF:
            driver.text("OFF", driver.width - 24, 20 + ROW_OFFSET)


class SettingView(View):
    __slots__ = ['lc']

    def __init__(self, local_changes: LocalChanges):
        self.lc = local_changes

    def write_to(self, driver: SH1106_I2C):
        from model import ATTR_OP_MODE

        driver.text("set", int(driver.width / 2) - 12, 56 + ROW_OFFSET)
        driver.fill_rect(0, ROW_OFFSET, driver.width, 2, 1)  # top
        driver.fill_rect(0, ROW_OFFSET, 2, driver.height, 1)  # left
        driver.fill_rect(driver.width - 2, ROW_OFFSET, 2, driver.height, 1)  # right
        driver.fill_rect(0, driver.height - 2 + ROW_OFFSET, int(driver.width / 2) - 12 - 4, 2, 1)  # bottom-left
        driver.fill_rect(int(driver.width / 2) + 12 + 4,
                         driver.height - 2 + ROW_OFFSET
                         , int(driver.width / 2) - 12 - 4, 2, 1)  # bottom-right

        wri = Writer(driver, freesans40, verbose=False)
        if self.lc.last_item == ATTR_OP_MODE:
            text = self.lc.operation_mode.upper()
            text_w = wri.stringlen(text)
            Writer.set_textpos(driver, 16 + ROW_OFFSET, int((driver.width - text_w) / 2) + 2)
            wri.printstring(text)
        else:
            Writer.set_textpos(driver, 16 + ROW_OFFSET, 26)
            wri.printstring("{0:.1f}".format(self.lc.temperature))
