#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import socket
import time

# ip addr add 192.168.10.1/24 dev eth0
# ifconfig eth0 192.168.10.255 netmask 255.255.255.0

def tcp_link_test():
    socket.setdefaulttimeout(3)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    try:
        s.connect(("192.168.10.41", 5005))
        s.settimeout(1)
        print(f"DAQ TCP socket up! {s}")
        time.sleep(3)
        #data = s.recv(19)
        #print(data)
    except TimeoutError:
        print(f"Timed out, DAQ TCP socket down")
    s.close() # for some reason closing tcp socket gives error
    #s.shutdown(socket.SHUT_RDWR)

def udp_link_test():
    socket.setdefaulttimeout(3)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.bind(("", 5005))
    try: # daq should be broadcasting at reasonable intervals
        for n in range(3):
            data = s.recvfrom(19)
            print(f'Received', data)
        print(f"DAQ UDP socket up! {s}")
    except TimeoutError:
        print(f"Timed out, DAQ UDP socket down")
    s.close()

def usb_link_test():
    socket.setdefaulttimeout(3)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    try:
        s.connect(("192.168.10.41", 5005))
        print(f"DAQ TCP socket up! {s}")
        #s.settimeout(20)
        #data = s.recv(19)
        #print(data)
    except TimeoutError:
        print(f"Timed out, DAQ TCP socket down")
    s.close() # for some reason closing tcp socket gives error

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--udp", action='store_true',
        help="run daq udp socket link test",
    )
    parser.add_argument("-t", "--tcp", action='store_true',
        help="run daq tcp socket link test",
    )
    args = parser.parse_args()

    if (args.udp):
        udp_link_test()
    if (args.tcp):
        tcp_link_test()
