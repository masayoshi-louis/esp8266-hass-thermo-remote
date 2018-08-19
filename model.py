import utime as time

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
    __slots__ = [ATTR_SETPOINT, ATTR_CURRENT_TEMPERATURE, ATTR_OP_MODE, ATTR_STATE, 'listeners']

    def __init__(self):
        self.listeners = []
        self.current_humidity = 0.0
        self.temperature = 0
        self.current_temperature = 0
        self.operation_mode = OP_MODE_OFF
        self.state = STATE_OFF

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

    def set_current_temperature(self, value: float):
        self.current_temperature = value
        print("[MODEL] current_temperature = {}".format(str(value)))
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
        'last_item'
    ]

    def __init__(self):
        self.setpoint = None
        self.op_mode = None
        self.last_ts = None
        self.last_item = None

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

    def setpoint(self, delta: float):
        if self.setpoint is None:
            current = getattr(instance, ATTR_SETPOINT)
        else:
            current = self.setpoint
        self.setpoint = current + delta
        self.last_ts = time.ticks_ms()
        self.last_item = ATTR_SETPOINT

    def reset(self):
        self.setpoint = None
        self.op_mode = None
        self.last_ts = None
        self.last_item = None

    def is_stable(self, delay: int):
        return time.ticks_ms() - self.last_ts > delay
