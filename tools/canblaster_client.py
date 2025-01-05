#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import socket
import time
import pickle

from communication.common import StoppableThread

# UDP client for tuning into (local) server broadcast of CAN message objects, not DAQ server

class UDPClient:
    def __init__(self, ip="127.0.0.1", port=5222, disp_flag=True):
        self.ip = ip
        self.port = port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        sock.bind((ip, port))
        self.sock = sock

        # Main thread for receiving from UDP broadcast
        self.recv_thread = StoppableThread(target=self.recv_poll)

        # For writing to file
        # TODO add child threads like writing to file, pushing to drive
        #self.file_queue = Queue()
        #self.file_thread = StoppableThread(target=self.file_poll)

    def start_threads(self):
        self.recv_thread.start()

    def stop_threads(self):
        self.recv_thread.stop()

    def recv_poll(self):
        while not self.recv_thread.stopped():
            try:
                data, server = self.sock.recvfrom(1024)
                msg = pickle.loads(data)
                #self.file_queue.put(msg)
                print(f'{msg}')
            except socket.timeout:
                print('REQUEST TIMED OUT')
        self.recv_thread.signal_stopped()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-i', "--ip", default="127.0.0.1", type=str,
        help="client ip (default 127.0.0.1) (don't mess with this)",
    )
    parser.add_argument('-p', "--port", default=5222, type=int,
        help="client port (default 5222) (edit udp_server.py to add new ports)",
    )
    parser.add_argument("--no-disp", action='store_true',
        help="don't print messages to terminal",
    )
    args = parser.parse_args()

    client = UDPClient(args.ip, args.port, disp_flag=not args.no_disp)
    try:
        client.start_threads()
        client.recv_thread._stop_event.wait() # wait without blocking KeyboardInterrupt
    except KeyboardInterrupt:
        client.stop_threads()
        #sys.exit(1)
