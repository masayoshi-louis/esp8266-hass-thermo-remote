from button import ContinuousButton, GenericButton
from config import *
from debounce_event import BUTTON_DEFAULT_HIGH, BUTTON_PUSHBUTTON, BUTTON_SET_PULLUP
from model import instance as model


class Controller:
    __slots__ = ['__refresh_display', '__btn1', '__btn2', '__btn3', '__btn4']

    def __init__(self):
        self.__refresh_display = False
        model.add_listener(self.__on_model_updated)
        self.__btn1 = GenericButton(pin=PIN_BTN_1,
                                    mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                    repeat=300)
        self.__btn2 = GenericButton(pin=PIN_BTN_2,
                                    mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                    repeat=300)
        self.__btn3 = ContinuousButton(pin=PIN_BTN_3,
                                       mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                       interval=250)
        self.__btn4 = ContinuousButton(pin=PIN_BTN_4,
                                       mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                       interval=250)

    def loop(self):
        self.__btn1.loop()
        self.__btn2.loop()
        self.__btn3.loop()
        self.__btn4.loop()

    def __on_model_updated(self):
        self.__refresh_display = True
