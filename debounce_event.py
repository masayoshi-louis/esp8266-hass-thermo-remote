import utime as time
from machine import Pin
from micropython import const

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
    __slots__ = [
        '_mode',
        '_default_status',
        '_status',
        '_delay',
        '_repeat',
        '_pin',
        '_ready',
        '_reset_count',
        '_event_start',
        '_event_length',
        '_event_count',
        '_cb'
    ]

    def __init__(self, pin: int,
                 mode: int = BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH,
                 delay: int = DEBOUNCE_DELAY,
                 repeat: int = REPEAT_DELAY):
        self._mode = mode & 0x01
        self._default_status = (mode & BUTTON_DEFAULT_HIGH) > 0
        self._status = self._default_status
        self._delay = delay
        self._repeat = repeat
        self._ready = False
        self._reset_count = True
        self._event_start = 0
        self._event_length = 0
        self._event_count = 0
        self._cb = None
        if pin == 16:
            if self._default_status:
                self._pin = Pin(pin, Pin.IN)
            else:
                raise Exception  # there's no Pin.PULL_DOWN
        else:
            if mode & BUTTON_SET_PULLUP > 0:
                self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
            else:
                self._pin = Pin(pin, Pin.IN)

    def set_callback(self, cb):
        self._cb = cb

    @property
    def pressed(self) -> bool:
        return self._status != self._default_status

    @property
    def event_length(self) -> int:
        return self._event_length

    @property
    def event_count(self) -> int:
        return self._event_count

    def loop(self) -> int:
        event = EVENT_NONE

        if self._read() != self._status:
            # Debounce
            start = time.ticks_ms()
            while time.ticks_ms() - start < self._delay:
                time.sleep_ms(1)

            if self._read() != self._status:
                self._status = not self._status

                if self._mode == BUTTON_SWITCH:
                    event = EVENT_CHANGED
                else:
                    if self._status == self._default_status:  # released
                        self._event_length = time.ticks_ms() - self._event_start
                        self._ready = True
                    else:  # pressed
                        event = EVENT_PRESSED
                        self._event_start = time.ticks_ms()
                        self._event_length = 0
                        if self._reset_count:
                            self._event_count = 1
                            self._reset_count = False
                        else:
                            self._event_count += 1
                        self._ready = False

        if self._ready and (time.ticks_ms() - self._event_start > self._repeat):
            self._ready = False
            self._reset_count = True
            event = EVENT_RELEASED

        if event != EVENT_NONE and self._cb is not None:
            self._cb(event, self._event_count, self._event_length)

        return event

    def _read(self):
        return self._pin.value()
