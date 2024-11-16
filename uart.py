
import argparse
import serial
import serial.tools.list_ports
import sys
import time

def log(x):
    print(f'uart.py: {x}')

def connect(dev_path, baud_rate):
    dev = serial.Serial(dev_path, baud_rate) # uart baud
    if (not dev.is_open):
        raise RuntimeError("Failed to connect to %s" % (dev_path))
    log(dev)
    return dev

def receive(dev):
    log("Receiving from %s baud: %d (ctrl+c to quit)" % (dev.name, dev.baudrate))
    try:
        while True:
            x = dev.read(1) # one byte each for uart
            try:
                sys.stdout.write(x.decode("ascii"))
                sys.stdout.flush()
            except Exception as e:
                log(e)
                log(x)
    except KeyboardInterrupt:
        pass

def list_devices():
    s = ""
    for i,p in enumerate(serial.tools.list_ports.comports()):
        s += " (%2d) %s" % (i, str(p))
    return s

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action='store_true',
        help="list serial devices",)
    parser.add_argument("-d", "--device", default='',
        help="path to device e.g. /dev/ttyUSB0, COM7",)
    parser.add_argument("-b", "--baud", default=115200, type=int,
        help="UART baud rate (default 115200)",)

    print('Python', sys.version, 'on', sys.platform)
    args = parser.parse_args()
    if (args.list):
        log(list_devices())
    if (not args.device):
        for i,p in enumerate(serial.tools.list_ports.comports()):
            if (any(x in p.description.lower() for x in ["uart", "serial", "ttl"])):
                log("Selected %s" % (str(p)))
                args.device = p.device
                break
    if (not args.device):
        raise RuntimeError("No serial port found. Specify path with --device {path}. Available devices: %s" % (list_devices()))

    dev = connect(args.device, args.baud)
    assert(dev.is_open)
    receive(dev)
