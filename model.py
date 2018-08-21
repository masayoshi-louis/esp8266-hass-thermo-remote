import utime as time

from hass import ThermostatAPI

OP_MODE_OFF = 'off'
OP_MODE_HEAT = 'heat'

STATE_OFF = 'off'
STATE_HEAT = 'heat'
STATE_IDLE = 'idle'

instance = None

ATTR_SETPOINT = 'temperature'
ATTR_CURRENT_TEMPERATURE = 'current_temperature'
ATTR_OP_MODE = 'operation_mode'
ATTR_STATE = 'state'


class SensorSample:
    __slots__ = ['t', 'h', 'p']

    def __init__(self, temperature: float, humidity: float, pressure: float):
        self.t = temperature
        self.h = humidity
        self.p = pressure


class ThermostatModel:
    __slots__ = ['temperature', 'current_temperature', 'operation_mode', 'state', 'sensor_sample', 'listeners']

    def __init__(self):
        self.listeners = []
        self.temperature = 0
        self.current_temperature = 0
        self.operation_mode = OP_MODE_OFF
        self.state = STATE_OFF
        self.sensor_sample = None

    def update(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)
        self.notify_listeners()

    def update_by_mqtt(self, topic: str, value: str):
        attr = topic[topic.rfind('/') + 1:]
        if attr in {ATTR_SETPOINT, ATTR_CURRENT_TEMPERATURE}:
            v = float(value)
            setattr(self, attr, v)
        elif attr in {ATTR_OP_MODE, ATTR_STATE}:
            v = value
            if v.startswith('"'):
                v = v[1:]
            if v.endswith('"'):
                v = v[:-1]
            setattr(self, attr, v)
        print("[MODEL] {} = {}".format(attr, str(v)))
        self.notify_listeners()

    def update_sensor_sample(self, value: SensorSample):
        self.sensor_sample = value
        self.current_temperature = self.sensor_sample.t
        self.notify_listeners()

    def add_listener(self, l):
        self.listeners.append(l)

    def notify_listeners(self):
        for notify in self.listeners:
            notify()


def init(init_data: dict):
    global instance
    instance = ThermostatModel()
    instance.update(init_data)


class LocalChanges:
    __slots__ = [
        'temperature',
        'operation_mode',
        'last_ts',
        'last_item',
        'max_t',
        'min_t'
    ]

    def __init__(self, max_temp: float, min_temp: float):
        self.temperature = None
        self.operation_mode = None
        self.last_ts = None
        self.last_item = None
        self.max_t = max_temp
        self.min_t = min_temp

    def enter_op_mode_setting(self) -> bool:
        return self._enter_setting(ATTR_OP_MODE)

    def enter_temperature_setting(self) -> bool:
        return self._enter_setting(ATTR_SETPOINT)

    def _enter_setting(self, item: str) -> bool:
        if self.last_item == item:
            return True
        else:
            self.last_item = item
            self.last_ts = time.ticks_ms()
            setattr(self, item, getattr(instance, item))
            return False

    def flip_op_mode(self):
        if self.last_item != ATTR_OP_MODE:
            raise Exception
        # flip mode
        if self.operation_mode == OP_MODE_OFF:
            self.operation_mode = OP_MODE_HEAT
        else:
            self.operation_mode = OP_MODE_OFF
        self.last_ts = time.ticks_ms()

    def setpoint_add(self, delta: float):
        if self.last_item != ATTR_SETPOINT:
            raise Exception
        self.temperature = min(max(self.temperature + delta, self.min_t), self.max_t)
        self.last_ts = time.ticks_ms()

    def save_to(self, api: ThermostatAPI):
        if self.operation_mode is not None:
            if self.operation_mode == OP_MODE_OFF:
                api.turn_off()
            else:
                api.set_heat_mode()
        if self.temperature is not None:
            api.set_temperature(self.temperature)

    def reset(self):
        self.temperature = None
        self.operation_mode = None
        self.last_ts = None
        self.last_item = None

    @property
    def is_changed(self) -> bool:
        return self.last_ts is not None

    def is_stable(self, delay: int) -> bool:
        return time.ticks_ms() - self.last_ts > delay
