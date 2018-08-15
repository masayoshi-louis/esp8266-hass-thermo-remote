OP_MODE_OFF = 'off'
OP_MODE_HEAT = 'heat'

STATE_OFF = 'off'
STATE_HEAT = 'heat'
STATE_IDLE = 'idle'


instance = None


class ThermostatModel:
    __slots__ = ['t_setpoint', 't_current', 'h_current', 'op_mode', 'state']

    def __init__(self, t_setpoint, t_current, h_current, op_mode, state):
        self.t_setpoint = t_setpoint
        self.t_current = t_current
        self.h_current = h_current
        self.op_mode = op_mode
        self.state = state


def init():  # TODO
    global instance
    instance = ThermostatModel(0, 0, 0)
