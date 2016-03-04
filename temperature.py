#!/usr/bin/env python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
# Modified by: Donald Merand for Explo (http://www.explo.org)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import time, subprocess
import toml

import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855



# Grab config information from the log file
with open("/home/pi/raspberry-pi-temperature-monitor/config.toml") as conffile:
  conf = toml.loads(conffile.read())

# Define a function to convert celsius to fahrenheit.
def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0

# Set up logging if applicable
LOGFORMAT = "%(asctime)s\t%(message)s"
if conf.get('log_file'):
  log_file = conf.get('log_file')
  log_level = conf.get('log_level')
  if log_level == 'DEBUG':
    logging.basicConfig(filename=log_file, format=LOGFORMAT, level=logging.DEBUG)
  else:
    logging.basicConfig(filename=log_file, format=LOGFORMAT, level=logging.INFO)
  print("Logging to {0}".format(log_file))
else:
  logging.basicConfig(level=logging.INFO, format=LOGFORMAT)

# Set up the poll rate
if conf.get('poll_rate'):
  poll_rate = conf.get('poll_rate')
else:
  poll_rate = 10 #seconds

# Uncomment one of the blocks of code below to configure your Pi to use
# software or hardware SPI.

# Raspberry Pi software SPI configuration.
sensor = MAX31855.MAX31855(conf['pi']['CLK'], conf['pi']['CS'], conf['pi']['DO'])
# Raspberry Pi hardware SPI configuration.
#sensor = MAX31855.MAX31855(spi=SPI.SpiDev(conf['pi']['SPI_PORT'], conf['pi']['SPI_DEVICE']))

# Grab our (wireless) IP address so that we can send a link to the webcam if
# the temp is too high
ip_command = "ifconfig | awk 'BEGIN{ORS=\"\"}/wlan0/{getline;gsub(/addr:/,\"\",$2);print $2}'"
my_ip = str(subprocess.check_output(ip_command, shell=True))


# Loop measurements every second.
while True:
  temp = sensor.readTempC()
  #internal = sensor.readInternalC()
  logging.info("{0:0.3F}*C\t{1:0.3F}*F".format(temp, c_to_f(temp)))
  #print '    Internal Temperature: {0:0.3F}*C / {1:0.3F}*F'.format(internal, c_to_f(internal))
  if temp > conf['temp']['max']:
    warning_text = "WARNING: Laser Cutter is hot, potential fire risk: {0:0.3F}*F. Webcam: http://{1}:8081".format(c_to_f(temp), my_ip)
    logging.warning(warning_text)
    subprocess.call(["/usr/local/bin/hipchat", warning_text])
    time.sleep(10) # wait 10 seconds
  if temp < conf['temp']['min']:
    warning_text = "WARNING: Laser Cutter is being exposed to freezing temperatures: {0:0.3F}*F. Webcam: http://{1}:8081".format(c_to_f(temp), my_ip)
    logging.warning(warning_text)
    subprocess.call(["/usr/local/bin/hipchat", warning_text])
    time.sleep(60 * 5) # wait 5 minutes
  else:
    time.sleep(poll_rate) # normally check every 1 seconds
