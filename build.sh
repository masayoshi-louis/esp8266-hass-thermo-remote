PROJ_DIR=`pwd`
MPY_DIR=$PROJ_DIR/../micropython/ports/esp8266

cd $MPY_DIR
make clean-frozen
micropython -m upip install -p modules micropython-urequests
micropython -m upip install -p modules micropython-umqtt.simple
micropython -m upip install -p modules micropython-struct

cd $PROJ_DIR

cp -t ../micropython/ports/esp8266/modules \
  sys_status.py \
  debounce_event.py \
  button.py \
  bme280.py \
  sht31.py \
  tsl2561.py \
  hass.py \
  model.py \
  mqtt.py \
  ssd1306.py \
  sh1106.py \
  writer.py \
  wifi.py \
  wifi_init.py \
  controller.py \
  app.py

cp -r font ../micropython/ports/esp8266/modules

cd $MPY_DIR
make clean
make
