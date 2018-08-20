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
        'setpoint',
        'op_mode',
        'last_ts',
        'last_item',
        'max_t',
        'min_t'
    ]

    def __init__(self, max_temp: float, min_temp: float):
        self.setpoint = None
        self.op_mode = None
        self.last_ts = None
        self.last_item = None
        self.max_t = max_temp
        self.min_t = min_temp

    def flip_op_mode(self):
        if self.op_mode is None:
            current = getattr(instance, ATTR_OP_MODE)
        else:
            current = self.op_mode
        # flip mode
        if current == OP_MODE_OFF:
            self.op_mode = OP_MODE_HEAT
        else:
            self.op_mode = OP_MODE_OFF
        self.last_ts = time.ticks_ms()
        self.last_item = ATTR_SETPOINT

    def setpoint_add(self, delta: float):
        if self.setpoint is None:
            current = getattr(instance, ATTR_SETPOINT)
        else:
            current = self.setpoint
        self.setpoint = min(max(current + delta, self.min_t), self.max_t)
        self.last_ts = time.ticks_ms()
        self.last_item = ATTR_SETPOINT

    def save_to(self, api: ThermostatAPI):
        if self.op_mode is not None:
            if self.op_mode == OP_MODE_OFF:
                api.turn_off()
            else:
                api.set_heat_mode()
        if self.setpoint is not None:
            api.set_temperature(self.setpoint)
        # clear local changes
        self.reset()

    def reset(self):
        self.setpoint = None
        self.op_mode = None
        self.last_ts = None
        self.last_item = None

    @property
    def is_changed(self) -> bool:
        return self.last_ts is not None

    def is_stable(self, delay: int) -> bool:
        return time.ticks_ms() - self.last_ts > delay
