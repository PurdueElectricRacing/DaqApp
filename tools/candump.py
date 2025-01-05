#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# dump CAN

import argparse
import time
from communication.canbus_backend import CANBusUSB, CANBusUDP

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-m', "--mode", default="usb",
        help="backend: usb/udp/tcp",
    )
    parser.add_argument('-t', "--timeout", default=0, type=float,
        help="timeout (sseconds)",
    )
    parser.add_argument('-n', "--node", default="",
        help="filter node (tx)",
    )
    args = parser.parse_args()
    timeout = args.timeout

    bus = CANBusUSB if args.mode == "usb" else CANBusUDP
    cb = bus()
    cb.connect()
    assert(cb.connected())

    cb.start_thread()
    try:
        start = time.time()
        while (not timeout) or (time.time() - start < timeout):
            msg = cb.receive_decoded_message(timeout=1)
            if (msg):
                if (not args.node or (args.node and msg.sender.lower() == args.node.lower())):
                    print(msg)
    except KeyboardInterrupt:
        pass
    cb.stop_thread()
