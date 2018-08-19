import utime as time
from micropython import const

from debounce_event import *

BUTTON_EVENT_NONE = const(0)
BUTTON_EVENT_PRESSED = const(1)
BUTTON_EVENT_CLICK = const(2)
BUTTON_EVENT_DBLCLICK = const(3)
BUTTON_EVENT_LNGCLICK = const(4)
BUTTON_EVENT_LNGLNGCLICK = const(5)
BUTTON_EVENT_TRIPLECLICK = const(6)
BUTTON_EVENT_N_CLICK = const(8)

BUTTON_LNGCLICK_DELAY = const(1000)
BUTTON_LNGLNGCLICK_DELAY = const(10000)

BUTTON_CONTINUOUS_INTERVAL = const(500)


def map_event(event, count, length) -> int:
    if event != EVENT_NONE:
        if event == EVENT_PRESSED:
            return BUTTON_EVENT_PRESSED
        if event == EVENT_CHANGED:
            return BUTTON_EVENT_CLICK
        if event == EVENT_RELEASED:
            if count == 1:
                if length > BUTTON_LNGLNGCLICK_DELAY:
                    return BUTTON_EVENT_LNGLNGCLICK
                if length > BUTTON_LNGCLICK_DELAY:
                    return BUTTON_EVENT_LNGCLICK
                return BUTTON_EVENT_CLICK
            if count == 2:
                return BUTTON_EVENT_DBLCLICK
            if count == 3:
                return BUTTON_EVENT_TRIPLECLICK
            if count < BUTTON_EVENT_N_CLICK:
                return BUTTON_EVENT_N_CLICK | count
    return BUTTON_EVENT_NONE


class GenericButton(DebounceEvent):
    def loop(self) -> int:
        event = super().loop()
        return map_event(event, self.event_count, self.event_length)

    def set_callback(self, cb):
        def raw_cb(e, c, l):
            cb(map_event(e, c, l))

        super().set_callback(raw_cb)


class ContinuousButton(DebounceEvent):
    __slots__ = ['__last_trigger', '__interval', '__my_cb']

    def __init__(self, interval: int = BUTTON_CONTINUOUS_INTERVAL, **kwargs):
        super().__init__(**kwargs)
        self.__interval = interval
        self.__last_trigger = 0
        self.__my_cb = None

    def loop(self) -> int:
        event = super().loop()
        if event == EVENT_PRESSED or (self.pressed and time.ticks_ms() - self.__last_trigger > self.__interval):
            self.__last_trigger = time.ticks_ms()
            if self.__my_cb is not None:
                self.__my_cb(BUTTON_EVENT_PRESSED)
            return BUTTON_EVENT_PRESSED
        return BUTTON_EVENT_NONE

    def set_callback(self, cb):
        self.__my_cb = cb
