# raspberry-pi-temperature-monitor
Monitors temperature + HipChats me when it's too high. Runs alongside a webcam server.

Basically just a modified version of [this Adafruit tutorial](https://learn.adafruit.com/max31855-thermocouple-python-library/overview)

Requires [this hipchat command line script](https://github.com/dmerand/dlm-dot-bin/blob/master/hipchat) to be set up properly + placed in `/usr/local/bin` .

You might want to copy `config.example.toml` to `config.toml` and check on some of those settings, particularly the HipChat stuff.
