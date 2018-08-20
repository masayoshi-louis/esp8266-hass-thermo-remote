from micropython import const

from button import ContinuousButton, GenericButton, BUTTON_EVENT_CLICK, BUTTON_EVENT_PRESSED
from config import *
from debounce_event import BUTTON_DEFAULT_HIGH, BUTTON_PUSHBUTTON, BUTTON_SET_PULLUP
from hass import ThermostatAPI
from model import OP_MODE_OFF, LocalChanges
from model import instance as model
from sys_status import instance as sys_status

ACTION_DELAY = const(2000)


class Controller:
    __slots__ = [
        '__hass_thermo_api',
        '__refresh_display',
        '__btn1',
        '__btn2',
        '__btn3',
        '__btn4',
        '__local_changes'
    ]

    def __init__(self, hass_thermo_api: ThermostatAPI, local_changes: LocalChanges):
        self.__hass_thermo_api = hass_thermo_api
        self.__refresh_display = False
        model.add_listener(self.__on_model_updated)
        self.__local_changes = local_changes
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
        # button actions
        self.__mode_btn_loop(self.__btn1)
        # TODO btn2
        self.__setpoint_up_btn_loop(self.__btn3)
        self.__setpoint_down_btn_loop(self.__btn4)
        # render view
        if self.__refresh_display:
            self.__render()
            self.__refresh_display = False
        # call home assistant services
        if self.__local_changes.is_changed and self.__local_changes.is_stable(ACTION_DELAY):
            try:
                self.__sync_to_hass()
                self.__refresh_display = True
            except OSError:
                sys_status.set_hass_api(False)

    def __render(self):
        # TODO
        pass

    def __sync_to_hass(self):
        if self.__local_changes.op_mode is not None:
            if self.__local_changes.op_mode == OP_MODE_OFF:
                self.__hass_thermo_api.turn_off()
            else:
                self.__hass_thermo_api.set_heat_mode()
        if self.__local_changes.setpoint is not None:
            self.__hass_thermo_api.set_temperature(self.__local_changes.setpoint)
        # clear local changes
        self.__local_changes.reset()

    def __on_model_updated(self):
        self.__refresh_display = True

    def __mode_btn_loop(self, btn: GenericButton):
        if btn.loop() == BUTTON_EVENT_CLICK:
            self.__local_changes.flip_op_mode()
            self.__refresh_display = True

    def __setpoint_up_btn_loop(self, btn: ContinuousButton):
        if btn.loop() == BUTTON_EVENT_PRESSED:
            self.__local_changes.setpoint_add(0.5)
            self.__refresh_display = True

    def __setpoint_down_btn_loop(self, btn: ContinuousButton):
        if btn.loop() == BUTTON_EVENT_PRESSED:
            self.__local_changes.setpoint_add(-0.5)
            self.__refresh_display = True
