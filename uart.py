
import serial
import time
import sys

dev_path = "/dev/ttyUSB0"
ser = serial.Serial(dev_path, 115200) # uart baud
assert(ser.is_open)

try:
    while True:
        x = ser.read(1) # one byte each for uart
        sys.stdout.write(x.decode("ascii"))
        sys.stdout.flush()
except KeyboardInterrupt:
    pass
