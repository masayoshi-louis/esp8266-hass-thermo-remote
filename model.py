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
ATTR_CURRENT_HUMIDITY = 'current_humidity'


class ThermostatModel:
    __slots__ = [ATTR_SETPOINT, ATTR_CURRENT_TEMPERATURE, ATTR_OP_MODE, ATTR_STATE, ATTR_CURRENT_HUMIDITY, 'listeners']

    def __init__(self):
        self.listeners = []

    def update(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)
        for notify in self.listeners:
            notify()

    def update_by_mqtt(self, topic: str, value: str):
        attr = topic[topic.rfind('/') + 1:]
        if attr in {ATTR_SETPOINT, ATTR_CURRENT_TEMPERATURE}:
            setattr(self, attr, float(value))
        elif attr in {ATTR_OP_MODE, ATTR_STATE}:
            setattr(self, attr, value)
        for notify in self.listeners:
            notify()

    def add_listener(self, l):
        self.listeners.append(l)


def init(init_data: dict):
    global instance
    instance = ThermostatModel()
    instance.update(init_data)
