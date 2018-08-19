from micropython import const

from debounce_event import *

BUTTON_EVENT_NONE = const(0)
BUTTON_EVENT_PRESSED = const(1)
BUTTON_EVENT_RELEASED = const(2)
BUTTON_EVENT_CLICK = const(2)
BUTTON_EVENT_DBLCLICK = const(3)
BUTTON_EVENT_LNGCLICK = const(4)
BUTTON_EVENT_LNGLNGCLICK = const(5)
BUTTON_EVENT_TRIPLECLICK = const(6)

BUTTON_LNGCLICK_DELAY = const(1000)
BUTTON_LNGLNGCLICK_DELAY = const(10000)


class Button(DebounceEvent):

    def loop(self) -> int:
        event = super().loop()
        if event != EVENT_NONE:
            if event == EVENT_PRESSED:
                return BUTTON_EVENT_PRESSED
            if event == EVENT_CHANGED:
                return BUTTON_EVENT_CLICK
            if event == EVENT_RELEASED:
                if self.event_count == 1:
                    if self.event_length > BUTTON_LNGLNGCLICK_DELAY:
                        return BUTTON_EVENT_LNGLNGCLICK
                    if self.event_length > BUTTON_LNGCLICK_DELAY:
                        return BUTTON_EVENT_LNGCLICK
                if self.event_count == 2:
                    return BUTTON_EVENT_DBLCLICK
                if self.event_count == 3:
                    return BUTTON_EVENT_TRIPLECLICK
        return BUTTON_EVENT_NONE
