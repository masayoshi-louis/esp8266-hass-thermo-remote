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


class ThermostatModel:
    __slots__ = [ATTR_SETPOINT, ATTR_CURRENT_TEMPERATURE, ATTR_OP_MODE, ATTR_STATE, 'current_humidity', 'listeners']

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
            setattr(self, attr, float(value))
        elif attr in {ATTR_OP_MODE, ATTR_STATE}:
            setattr(self, attr, value)
        self.notify_listeners()

    def set_current_humidity(self, value: float):
        self.current_humidity = value
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
