#!/usr/bin/env sh

sudo apt-get update
sudo apt-get install build-essential python-dev python-pip python-smbus git

sudo pip install RPi.GPIO

cd $HOME
git clone https://github.com/adafruit/Adafruit_Python_MAX31855.git
cd Adafruit_Python_MAX31855
sudo python setup.py install

sudo pip install toml
