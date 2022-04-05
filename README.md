# Data Acquisition Application
A PyQt app used to modify tracked variables and display live data on the car.

## Getting Started
1. Configure the dashboard.json to point to the required file paths
2. Install the required python packages with the command `pip install -r requirements.txt`
3. Connect a USB Canable
4. Run main.py

## Wireless Logging
Files contained in the raspi folder need to go on the raspberry pi under /home/pi/DAQ. Create a directory /home/pi/DAQ/logs as well. Move the daq service and daq logging services to /etc/systemd/system/. To enable, use `sudo systemctl enable daq_telem_service.service` and repeat for the logging service. Add the following line to /etc/rc.local before exit 0: `/home/pi/DAQ/canup.sh`.

The logger will log CAN frames as long as GPIO 26 is pulled to 3.3 V. It will create a new log file every 15 minutes while logging is enabled.

The server accepts a tcp connection on port 8080 and is meant to be interfaced with via /communication/client.py.

To trigger circle ci to do a build:
git tag #.#.#
git push origin #.#.#