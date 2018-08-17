import machine
import os

import app

WIFI_SETUP_FLAG = 'wifi_setup.flag'

if WIFI_SETUP_FLAG not in os.listdir():
    from wifi import wifi_connect, disable_wifi_ap
    from wifi_cfg import *
    from config import HOSTNAME

    disable_wifi_ap()
    wifi_connect(SSID, PASSWORD, hostname=HOSTNAME)

    f = open(WIFI_SETUP_FLAG, 'w')
    f.write(SSID)
    f.close()

    machine.reset()

app.main()
