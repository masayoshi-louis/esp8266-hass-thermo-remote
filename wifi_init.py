import os

import machine

WIFI_SETUP_FLAG = 'wifi_setup.flag'


def init_wifi(reset: bool = False):
    if WIFI_SETUP_FLAG not in os.listdir():
        from wifi import wifi_connect, disable_wifi_ap
        from wifi_cfg import SSID, PASSWORD
        from config import HOSTNAME

        disable_wifi_ap()
        wifi_connect(SSID, PASSWORD, hostname=HOSTNAME)

        f = open(WIFI_SETUP_FLAG, 'w')
        f.write(SSID)
        f.close()

        if reset:
            machine.reset()
