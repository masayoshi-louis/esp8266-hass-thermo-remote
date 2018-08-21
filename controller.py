from micropython import const

import display
from button import ContinuousButton, GenericButton, BUTTON_EVENT_CLICK, BUTTON_EVENT_PRESSED
from config import *
from debounce_event import BUTTON_DEFAULT_HIGH, BUTTON_PUSHBUTTON, BUTTON_SET_PULLUP
from hass import ThermostatAPI
from model import LocalChanges
from sys_status import instance as sys_status

ACTION_DELAY = const(2000)


class Controller:
    __slots__ = [
        'hass_thermo_api',
        'refresh_display',
        'btn1',
        'btn2',
        'btn3',
        'btn4',
        'local_changes'
    ]

    def __init__(self, hass_thermo_api: ThermostatAPI, local_changes: LocalChanges):
        from model import instance as model
        self.hass_thermo_api = hass_thermo_api
        self.refresh_display = False
        model.add_listener(self._on_model_updated)
        self.local_changes = local_changes
        self.btn1 = GenericButton(pin=PIN_BTN_1,
                                  mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                  repeat=300)
        self.btn2 = GenericButton(pin=PIN_BTN_2,
                                  mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                  repeat=300)
        self.btn3 = ContinuousButton(pin=PIN_BTN_3,
                                     mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                     interval=250)
        self.btn4 = ContinuousButton(pin=PIN_BTN_4,
                                     mode=BUTTON_PUSHBUTTON | BUTTON_DEFAULT_HIGH | BUTTON_SET_PULLUP,
                                     interval=250)

    def loop(self):
        # button actions
        self._mode_btn_loop(self.btn1)
        # TODO btn2
        self._setpoint_up_btn_loop(self.btn3)
        self._setpoint_down_btn_loop(self.btn4)
        # render view
        if self.refresh_display:
            self._render()
            self.refresh_display = False
        # call home assistant services
        if self.local_changes.is_changed and self.local_changes.is_stable(ACTION_DELAY):
            try:
                self.local_changes.save_to(self.hass_thermo_api)
                self.refresh_display = True
            except OSError:
                sys_status.set_hass_api(False)

    def _render(self):
        if self.local_changes.is_changed:
            display.instance.render(display.SettingView(self.local_changes))
        else:
            display.instance.render(display.NormalView())

    def _on_model_updated(self):
        self.refresh_display = True

    def _mode_btn_loop(self, btn: GenericButton):
        if btn.loop() == BUTTON_EVENT_CLICK:
            if self.local_changes.enter_op_mode_setting():
                self.local_changes.flip_op_mode()
            print("[BTN] mode button click, set mode to", self.local_changes.op_mode)
            self.refresh_display = True

    def _setpoint_up_btn_loop(self, btn: ContinuousButton):
        if btn.loop() == BUTTON_EVENT_PRESSED:
            if self.local_changes.enter_temperature_setting():
                self.local_changes.setpoint_add(0.5)
            print("[BTN] temp-up button pressed, set temperature to", self.local_changes.setpoint)
            self.refresh_display = True

    def _setpoint_down_btn_loop(self, btn: ContinuousButton):
        if btn.loop() == BUTTON_EVENT_PRESSED:
            if self.local_changes.enter_temperature_setting():
                self.local_changes.setpoint_add(-0.5)
            print("[BTN] temp-down button pressed, set temperature to", self.local_changes.setpoint)
            self.refresh_display = True
