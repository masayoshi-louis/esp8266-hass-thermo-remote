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
