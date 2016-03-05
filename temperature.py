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


# Set up logging if applicable
LOGFORMAT = "%(asctime)s\t%(message)s"
if conf.get('log_file'):
  if conf.get('log_level') == 'DEBUG':
    logging.basicConfig(filename=conf['log_file'], format=LOGFORMAT, level=logging.DEBUG)
  else:
    # Default to INFO-level logging
    logging.basicConfig(filename=conf['log_file'], format=LOGFORMAT, level=logging.INFO)
  print("Logging to {0}".format(conf['log_file']))
else:
  # Just log to STDOUT
  logging.basicConfig(level=logging.INFO, format=LOGFORMAT)


# Set up the temperature poll rate
if conf.get('poll_rate'):
  poll_rate = conf.get('poll_rate')
else:
  # Default to 10 seconds if none is set
  poll_rate = 10


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


# We sometimes get false freezing measurements on startup. So we double-check
# for freezing temps
might_be_freezing = None

# Loop measurements every second.
while True:
  # Rotate log file
  if conf.get('log_file'):
    log_size = os.stat(conf.get('log_file')).st_size 

    if conf.get('log_file_rotate_size') == None:
      log_file_rotate_size = 1000000 #10MB
    else
      log_file_rotate_size = conf['log_file_rotate_size']

    if log_size > conf.get('log_file_rotate_size'):
      # Store log in hipchat
      if conf.get('hipchat').get('token') and conf.get('hipchat').get('room'):
        subprocess.call(['/usr/local/bin/hipfile', "--token", conf['hipchat']['token'], "--room", conf['hipchat']['room'], "--path", conf.get('log_file'), "--message", 'Laser Cutter Temperature Log'])
      # Empty log file
      with open(conf.get('log_file'), 'w'):
        pass


  # now do the temperature reading
  temp = sensor.readTempC()
  #internal = sensor.readInternalC()
  logging.info("{0:0.3F}*C\t{1:0.3F}*F".format(temp, c_to_f(temp)))

  if temp > conf['temp']['max']:
    warning_text = "WARNING: Laser Cutter is hot, potential fire risk: {0:0.3F}*F. Webcam: http://{1}:8081".format(c_to_f(temp), my_ip)
    logging.warning(warning_text)
    subprocess.call(["/usr/local/bin/hipchat", warning_text])
    time.sleep(10) # wait 10 seconds
  if temp < conf['temp']['min']:
    if might_be_freezing:
      might_be_freezing = None
      warning_text = "WARNING: Laser Cutter is being exposed to freezing temperatures: {0:0.3F}*F. Webcam: http://{1}:8081".format(c_to_f(temp), my_ip)
      logging.warning(warning_text)
      subprocess.call(["/usr/local/bin/hipchat", warning_text])
    else:
      might_be_freezing = True
    time.sleep(60 * 5) # wait 5 more minutes to be sure
  else:
    # Temperature is in normal range, wait regular polling amount + try again
    time.sleep(poll_rate)
