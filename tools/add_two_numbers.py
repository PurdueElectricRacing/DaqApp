#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# Add two numbers over CAN

import argparse
import random
from communication.canbus_backend import CANBusUSB, CANBusTCP

def add_two_numbers(canbus, node, x, y):
    UDS_CMD_SYS_TEST = 0x06
    data = (x & 0xffff) | (y & 0xffff) << 16
    canbus.send_uds_frame(node=node, cmd=UDS_CMD_SYS_TEST, data=data)
    msg = canbus.receive_uds_frame(node=node, timeout=3.0)
    z = (msg.data >> 32) & 0xffff
    return z

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-m', "--mode", default="usb",
        help="usb/udp/tcp",
    )
    args = parser.parse_args()
    node = args.node

    bus = CANBusUSB if (args.mode == "usb") else CANBusTCP
    canbus = bus(None, verbose=args.verbose)
    canbus.connect()
    assert(canbus.connected())
    canbus.start_thread()

    x = random.randint(0, 0xffff // 2)
    y = random.randint(0, 0xffff // 2)
    z = add_two_numbers(canbus, node, x, y)
    print("0x%04x + 0x%04x == 0x%04x" % (x, y, z))
    assert(x + y == z)

    canbus.stop_thread()
