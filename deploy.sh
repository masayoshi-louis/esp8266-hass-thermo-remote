cp -t ../micropython/ports/esp8266/modules app.py \
  bme280.py \
  hass.py \
  model.py \
  mqtt.py \
  ssd1306.py \
  thingflow.py \
  wifi.py \
  urequests.py \
  writer.py

cp -r font ../micropython/ports/esp8266/modules
cp -r umqtt ../micropython/ports/esp8266/modules

cd ../micropython/ports/esp8266
make

sudo esptool.py --port /dev/ttyUSB0 erase_flash
sudo make PORT=/dev/ttyUSB0 deploy
