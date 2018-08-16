./build.sh

PROJ_DIR=`pwd`
MPY_DIR=$PROJ_DIR/../micropython/ports/esp8266
cd $MPY_DIR

sudo esptool.py --port /dev/ttyUSB0 erase_flash
sudo make PORT=/dev/ttyUSB0 deploy
