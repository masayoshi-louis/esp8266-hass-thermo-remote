from micropython import const
from machine import Pin
import utime as time

BUTTON_PUSHBUTTON = const(0)
BUTTON_SWITCH = const(1)
BUTTON_DEFAULT_HIGH = const(2)
BUTTON_SET_PULLUP = const(4)

DEBOUNCE_DELAY = const(50)
REPEAT_DELAY = const(500)

EVENT_NONE = const(0)
EVENT_CHANGED = const(1)
EVENT_PRESSED = const(2)
EVENT_RELEASED = const(3)


class DebounceEvent:
    __slots__ = ['__mode', '__default_status', '__status', '__delay', '__repeat', '__pin', '__ready', '__reset_count',
                 '__event_start', '__event_length', '__event_count', '__cb']

    def __init__(self, pin: int,
                 mode: int = BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH,
                 delay: int = DEBOUNCE_DELAY,
                 repeat: int = REPEAT_DELAY,
                 callback=None):
        self.__mode = mode & 0x01
        self.__default_status = (mode & BUTTON_DEFAULT_HIGH) > 0
        self.__status = self.__default_status
        self.__delay = delay
        self.__repeat = repeat
        self.__ready = False
        self.__reset_count = True
        self.__event_start = 0
        self.__event_length = 0
        self.__event_count = 0
        self.__cb = callback
        if pin == 16:
            if self.__default_status:
                self.__pin = Pin(pin, Pin.IN)
            else:
                raise Exception  # there's no Pin.PULL_DOWN
        else:
            if mode & BUTTON_SET_PULLUP > 0:
                self.__pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            else:
                self.__pin = Pin(pin, Pin.IN)

    def loop(self) -> int:
        event = EVENT_NONE

        if self.__read() != self.__status:
            # Debounce
            start = time.ticks_ms()
            while time.ticks_ms() - start < self.__delay:
                time.sleep_ms(1)

            if self.__read() != self.__status:
                self.__status = not self.__status

                if self.__mode == BUTTON_SWITCH:
                    event = EVENT_CHANGED
                else:
                    if self.__status == self.__default_status:  # released
                        self.__event_length = time.ticks_ms() - self.__event_start
                        self.__ready = True
                    else:  # pressed
                        event = EVENT_PRESSED
                        self.__event_start = time.ticks_ms()
                        self.__event_length = 0
                        if self.__reset_count:
                            self.__event_count = 1
                            self.__reset_count = False
                        else:
                            self.__event_count += 1
                        self.__ready = False

        if self.__ready and (time.ticks_ms() - self.__event_start > self.__repeat):
            self.__ready = False
            self.__reset_count = True
            event = EVENT_RELEASED

        if event != EVENT_NONE and self.__cb is not None:
            self.__cb(event, self.__event_count, self.__event_length)

        return event

    def __read(self):
        return self.__pin.value()
