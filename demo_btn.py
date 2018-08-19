from button import *


def loop():
    b = GenericButton(pin=5, mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP, repeat=300)
    while 1:
        e = b.loop()
        if e == BUTTON_EVENT_PRESSED:
            print("press")
            continue
        if e == BUTTON_EVENT_CLICK:
            print("click")
        if e == BUTTON_EVENT_DBLCLICK:
            print("double click")
        if e == BUTTON_EVENT_TRIPLECLICK:
            print("triple click")
        if e & BUTTON_EVENT_N_CLICK > 0:
            n = e & (BUTTON_EVENT_N_CLICK - 1)
            print("{} click".format(n))
        if e == BUTTON_EVENT_LNGCLICK:
            print("long click")
        if e == BUTTON_EVENT_LNGLNGCLICK:
            print("long long click")
        if e != BUTTON_EVENT_NONE:
            print("")
