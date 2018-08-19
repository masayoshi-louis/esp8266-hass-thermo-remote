from machine import I2C

instance = None


class Display:
    __slots__ = ['i2c']

    def __init__(self, i2c: I2C):
        self.i2c = i2c

    def render(self):
        pass


def init(i2c: I2C):
    global instance
    instance = Display(i2c=i2c)
