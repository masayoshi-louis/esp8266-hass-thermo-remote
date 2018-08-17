PROJ_DIR=`pwd`
MPY_DIR=$PROJ_DIR/../micropython/ports/esp8266

cd $MPY_DIR
make clean-frozen
micropython -m upip install -p modules micropython-urequests
micropython -m upip install -p modules micropython-umqtt.robust
micropython -m upip install -p modules micropython-umqtt.simple

cd $PROJ_DIR

cp -t ../micropython/ports/esp8266/modules \
  app.py \
  bme280.py \
  hass.py \
  model.py \
  mqtt.py \
  ssd1306.py \
  thingflow.py \
  writer.py

cp -r font ../micropython/ports/esp8266/modules

cd $MPY_DIR
make clean
make
