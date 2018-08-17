./build.sh

PROJ_DIR=`pwd`
MPY_DIR=$PROJ_DIR/../micropython/ports/esp8266
TTY_PORT=/dev/ttyUSB0

cd $MPY_DIR

sudo esptool.py --port $TTY_PORT erase_flash
sudo make PORT=$TTY_PORT deploy

sudo ampy --port $TTY_PORT put config.py
sudo ampy --port $TTY_PORT put wifi.py

#sudo ampy --port $TTY_PORT put main.py
