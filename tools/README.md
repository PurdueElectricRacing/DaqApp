
### bootloader.py

- standalone module for flashing firmware over TCP/CAN

```
python3 bootloader.py --node main_module --mode tcp --path new_firmware.hex
python3 bootloader.py -n daq -m usb --stat --load-backup
```

See help message output of `python3 bootloader.py -h`


### candump.py

- Dump raw can messages from canable (USB) or DAQ's UDP broadcast

```
python3 candump.py -m usb
python3 candump.py -m udp --timeout 5.0
```

- TODO add save to file feature, message filtering feature


### canup.sh

- Script for setting up ip for DAQ UDP/TCP (to set static ip because it can't do dhcp) and socketcan for USB

```
./canup.sh usb
./canup.sh tcp
./canup.sh (all)
```

Related, `canstat.sh` will show link status.

You can then run `link_test.py` to check DAQ udp/tcp socket link status

```
./canstat.sh (all)
python3 link_test.py -u -t
```


### uart.py

- UART to USB receiver (intended for reading UART with a UART-to-USB converter bridge)

```
python3 uart.py -r
python3 uart.py --receive --baud 115200 --device /dev/USB0
```

It will relay UART data onto terminal window

The script tries its best to automatically detect the USB device path, but you might have to specify it. Depending on the converter bridge used the device path would be something along the lines of /dev/ttyACM0, /dev/USB0, /dev/ttyS0 on Linux/Mac and COM6 or COM7 or COMX on windows.


### canblaster_server.py/canblaster_client.py

- Relay can messages from canable (USB) or DAQ's UDP broadcast onto a new UDP server

server:
```
python3 canblaster_server.py -m usb
```

client:
```
python3 canblaster_client.py
python3 canblaster_client.py --port 4444
```

To add a new client you have to add a new port in the port list in `udp_server.py` because python socket multicasting is weird. The server broadcasts on port 4269 so choose any other port than that one.

- TODO add child threads in client to actually do something useful, e.g. write to file and push the file to cloud

