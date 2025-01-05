#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import socket
import time
import pickle

from communication.canbus_backend import CANBusUSB, CANBusUDP

# UDP server for broadcasting of CAN message objects

def main(canbus):
    print(f"UDP SERVER: Kicking up UDP server for canbus {canbus}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 4269))
    print(f"UDP SERVER: Server: {server_socket}")
    try:
        last_time = time.time()
        addresses = [('127.0.0.1', 5222),]
        while True:
            msg = canbus.receive_message()
            if msg:
                data = pickle.dumps(msg)
                for address in addresses:
                    server_socket.sendto(data, address)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument("-m", "--mode", default="usb",
        help="usb/udp/tcp",
    )
    args = parser.parse_args()

    bus = CANBusUSB if args.mode == "usb" else CANBusUDP
    canbus = bus(None, verbose=args.verbose)
    canbus.connect()
    canbus.start_thread()
    main(canbus)
    canbus.stop_thread()
