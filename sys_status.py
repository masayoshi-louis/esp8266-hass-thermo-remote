import machine
from machine import Pin


class SystemStatus:
    __slots__ = ['sensor', 'hass_api', 'mqtt', 'led', 'boot']

    def __init__(self):
        self.sensor = False
        self.hass_api = False
        self.mqtt = False
        self.boot = True
        self.led = Pin(2, Pin.OUT)
        self._update_led()

    def set_sensor(self, v: bool):
        if self.sensor == v:
            return
        self.sensor = v
        self._on_update("Sensor", v)

    def set_hass_api(self, v: bool):
        if self.hass_api == v:
            return
        self.hass_api = v
        self._on_update("Home assistant API", v)

    def set_mqtt(self, v: bool):
        if self.mqtt == v:
            return
        self.mqtt = v
        self._on_update("MQTT client", v)

    def is_ok(self):
        return self.sensor and self.hass_api and self.mqtt

    def _on_update(self, item: str, v: bool):
        print("{} is{} OK".format(item, '' if v else ' not'))
        self._update_led()
        if not self.boot and not self.is_ok():
            machine.reset()

    def _update_led(self):
        self.led.value(self.is_ok())


instance = SystemStatus()
