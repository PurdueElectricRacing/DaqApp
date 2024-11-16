
import argparse
import serial
import serial.tools.list_ports
import sys
import time
from datetime import datetime
import struct
from construct import *

UART_FRAME_STARTCODE = 0xDEADBEEF
UART_FRAME_SIZE = 8

UART_COMMAND_HEARTBEAT =  0x1
UART_COMMAND_HELLOWORLD = 0x2

UartFrame = Struct(
    #"code" / Hex(Int32ul), # start code commented out bc we search for it already
    "tick" / Hex(Int32ul),
    "type" / Hex(Int32ul),
    "size" / Hex(Int32ul),
    "data" / Hex(Int32ul),
)

class UARTGateway:
    def __init__(self):
        self.dev = None

    def log(self, msg):
        print(f'UART: {msg}')

    def connect(self, dev_path, baud_rate):
        dev = serial.Serial(dev_path, baud_rate) # uart baud
        if (not dev.is_open):
            raise RuntimeError("Failed to connect to %s" % (dev_path))
        dev.timeout = 1
        self.dev = dev
        self.log(dev)
        assert(self.is_connected())

    def is_connected(self):
        return self.dev and self.dev.is_open

    def readfull(self, size):
        d = b''
        while len(d) < size:
            block = self.dev.read(size - len(d))
            if not block:
                raise RuntimeError("Expected %d bytes, got %d bytes" % (size,len(d)))
            d += block
        return d

    # for generic listening i.e. printing log messages to terminal
    def receive(self):
        self.log("Receiving from %s baud: %d (ctrl+c to quit)" % (self.dev.name, self.dev.baudrate))
        try:
            while True:
                try:
                    c = self.dev.read(1)  # one byte each for uart
                    self.stdout_msg(c)
                except KeyboardInterrupt:
                    return
                except Exception as e:
                    self.log(e)
                    self.log(c)
        except KeyboardInterrupt:
            pass

    def stdout_msg(self, c):
        sys.stdout.write(c.decode("ascii"))
        sys.stdout.flush()

    # for generic listening i.e. printing log messages to terminal
    def receive_timeout(self, timeout=1): # in seconds
        timeout_start = time.time()
        b = b''
        while time.time() < timeout_start + timeout:
            c = self.dev.read(1)
            self.stdout_msg(c)
            b += c
        return b

    def list_devices(self):
        for i,p in enumerate(serial.tools.list_ports.comports()):
            self.log(" (%2d) %s" % (i, str(p)))

    def write_frame(self, frame):
        self.dev.write(b"\xef\xbe\xad\xde") # start code
        self.dev.write(frame)

    def send_frame(self, type, data):
        frame = UartFrame.build(dict(
            tick = int(round((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())) & 0xffffffff, # unix time
            size = UART_FRAME_SIZE,
            type = type,
            data = data,
        ))
        self.write_frame(frame)

        response = self.receive_frame()
        assert(response.type == 0x20000000 | type & 0xffff)

    def receive_frame(self):
        reply = b''
        while True:
            if not reply or reply[-1] != 255:
                reply = b''
                reply += self.readfull(1)
                if reply != b"\xef":
                    self.stdout_msg(reply) # direct log messages to stdout
                    continue
            else:
                reply = b'\xef'
            reply += self.readfull(1)
            if reply != b"\xef\xbe":
                self.stdout_msg(reply)
                continue
            reply += self.readfull(1)
            if reply != b"\xef\xbe\xad":
                self.stdout_msg(reply)
                continue
            reply += self.readfull(1)
            cmdin = struct.unpack("<I", reply)[0]
            if (cmdin == UART_FRAME_STARTCODE):
                frame_data = self.readfull(UartFrame.sizeof())
                frame = UartFrame.parse(frame_data)
                self.log("RX Frame: %s" % str(frame))
                return frame

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action='store_true',
        help="list serial devices",)
    parser.add_argument("-d", "--device", default='',
        help="path to device e.g. /dev/ttyUSB0, COM7",)
    parser.add_argument("-b", "--baud", default=115200, type=int,
        help="UART baud rate (default 115200)",)
    parser.add_argument("-r", "--receive", action='store_true',
        help="generic uart listener (print messages to terminal)",)

    print('Python', sys.version, 'on', sys.platform)
    args = parser.parse_args()
    ug = UARTGateway()
    if (args.list):
        ug.list_devices()
    if (not args.device):
        for i,p in enumerate(serial.tools.list_ports.comports()):
            if (any(x in p.description.lower() for x in ["uart", "serial", "ttl"])):
                ug.log("Selected %s" % (str(p)))
                args.device = p.device
                break
    if (not args.device):
        ug.list_devices()
        raise RuntimeError("No serial port found. Specify path with --device {path}")

    ug.connect(args.device, args.baud)
    assert(ug.is_connected())

    if (args.receive):
        ug.receive()
    else:
        data = 0xcafebabe
        ug.send_frame(UART_COMMAND_HEARTBEAT, data)
        ug.send_frame(UART_COMMAND_HELLOWORLD, data)
        #ug.receive_timeout(1)  # message to terminal
