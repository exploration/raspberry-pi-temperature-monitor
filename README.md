# raspberry-pi-temperature-monitor
Monitors temperature + HipChats me when it's too high. Runs alongside a webcam server.

Basically just a modified version of [this Adafruit tutorial](https://learn.adafruit.com/max31855-thermocouple-python-library/overview)

Requires [this hipchat command line script](https://github.com/dmerand/dlm-dot-bin/blob/master/hipchat) to be set up properly + placed in `/usr/local/bin` . If you're using log files, you'll also want to install the `hipfile` example from the [hipchat-go library](https://github.com/tbruyelle/hipchat-go) into `/usr/local/bin` .

`setup.sh` does most of the setup, aside from copying in any necessary HipChat binaries/scripts. You might want to copy `config.example.toml` to `config.toml` and check on some of those settings, particularly the HipChat stuff.

Put this line into `/etc/rc.local` to make it run as a daemon-ish thing (assuming you cloned it from the default home directory on the Pi): `sudo /usr/bin/python /home/pi/raspberry-pi-temperature-monitor/temperature.py &`
