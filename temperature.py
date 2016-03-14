#!/usr/bin/env python
# Author: Donald Merand for Explo (http://www.explo.org)
# Some bits are from Adafruit (see README)

import logging, time, subprocess, os
import toml

import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855


# Define a function to convert celsius to fahrenheit.
def c_to_f(c):
  return c * 9.0 / 5.0 + 32.0

# Grab config information from the log file (TOML format)
with open("/home/pi/raspberry-pi-temperature-monitor/config.toml") as conffile:
  conf = toml.loads(conffile.read())

# Check for a parameter + use it, otherwise set a default value
# Returns a string value, typically used like:
#   some_param = config_check('some_param', 'default_value')
def config_check(param, default):
  if conf.get(param):
    return conf.get(param)
  else:
    return default


# Set up logging if applicable
LOGFORMAT = "%(asctime)s\t%(message)s"
if conf.get('log_file'):
  log_file_rotate_size = config_check('log_file_rotate_size', 10000000)
  if conf.get('log_level') == 'DEBUG':
    logging.basicConfig(filename=conf['log_file'], format=LOGFORMAT, level=logging.DEBUG)
  else:
    # Default to INFO-level logging
    logging.basicConfig(filename=conf['log_file'], format=LOGFORMAT, level=logging.INFO)
  print("Logging to {0}".format(conf['log_file']))
else:
  # Just log to STDOUT
  logging.basicConfig(level=logging.INFO, format=LOGFORMAT)


# Check if the log size is greater than our max allowable size.
# Send it to HipChat if it's too big, and clear it out
def rotate_log_file():
  if conf.get('log_file'):
    log_size = os.stat(conf.get('log_file')).st_size 

    if log_size > log_file_rotate_size:
      # Store log in hipchat
      if conf.get('hipchat').get('token') and conf.get('hipchat').get('room'):
        subprocess.call(['/usr/local/bin/hipfile', "--token", conf['hipchat']['token'], "--room", conf['hipchat']['room'], "--path", conf.get('log_file'), "--message", "{0} Temperature Log".format(device_name)])
      # Empty log file
      with open(conf.get('log_file'), 'w'):
        pass


# Set some default values
device_name = config_check('device_name', 'Unknown Device')
# Make sure the temperature has been out of range since the last period, to
# avoid spurious one-off temperature readings causing broadcasts
last_temp = None
poll_rate = config_check('poll_rate', 10)
# Set our temperature sensor based on the desired connection method
if conf.get('pi').get('connect_method') == "HARDWARE":
  sensor = MAX31855.MAX31855(spi=SPI.SpiDev(conf['pi']['SPI_PORT'], conf['pi']['SPI_DEVICE']))
else:
  # Default to software SPI
  sensor = MAX31855.MAX31855(conf['pi']['CLK'], conf['pi']['CS'], conf['pi']['DO'])


# Grab our (wireless) IP address so that we can send a link to the webcam if
# the temp is too high/low
ip_command = "ifconfig | awk 'BEGIN{ORS=\"\"}/wlan0/{getline;gsub(/addr:/,\"\",$2);print $2}'"
my_ip = str(subprocess.check_output(ip_command, shell=True))


# Loop measurements every second.
while True:
  rotate_log_file

  # now do the temperature reading
  temp = sensor.readTempC()
  #internal = sensor.readInternalC()
  logging.info("{0:0.3F}*C\t{1:0.3F}*F".format(temp, c_to_f(temp)))

  if temp > conf['temp']['max']:
    if last_temp > conf['temp']['max']:
      warning_text = "{0} WARNING: {1} is hot, potential fire risk: {2:0.3F}*F. Webcam: http://{3}?action=stream".format(conf.get('hipchat').get('notify_names'), device_name, c_to_f(temp), my_ip)
      logging.warning(warning_text)
      if conf.get('hipchat').get('room'):
        subprocess.call(["/usr/local/bin/hipchat", "-r", conf['hipchat']['room'], warning_text])
    time.sleep(30) #seconds
  if temp < conf['temp']['min'] :
    if last_temp < conf['temp']['min']:
      warning_text = "{0} WARNING: {1} is being exposed to freezing temperatures: {2:0.3F}*F. Webcam: http://{3}?action=stream".format(conf.get('hipchat').get('notify_names'), device_name, c_to_f(temp), my_ip)
      logging.warning(warning_text)
      if conf.get('hipchat').get('room'):
        subprocess.call(["/usr/local/bin/hipchat", "-r", conf['hipchat']['room'], warning_text])
    time.sleep(60 * 10) # wait 10 more minutes in this case to be sure
  else:
    # Temperature is in normal range, store it, wait regular polling amount + try again
    last_temp = temp
    time.sleep(poll_rate)
