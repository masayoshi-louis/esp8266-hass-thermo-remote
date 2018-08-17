./build.sh

PROJ_DIR=`pwd`
MPY_DIR=$PROJ_DIR/../micropython/ports/esp8266
TTY_PORT=/dev/ttyUSB0

cd $MPY_DIR

sudo esptool.py --port $TTY_PORT erase_flash
sudo make PORT=$TTY_PORT deploy

echo 'wait 10s'
sleep 10
echo 'uploading scripts'

cd $PROJ_DIR

sudo ampy -p $TTY_PORT put config.py
sudo ampy -p $TTY_PORT put wifi.py

if [ -f wifi_cfg.py ]
then
    sudo ampy -p $TTY_PORT put wifi_cfg.py
fi

sudo ampy -p $TTY_PORT put main.py
#sudo ampy -p $TTY_PORT put app.py

echo 'done!'
