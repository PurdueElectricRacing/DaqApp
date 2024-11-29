import atexit
import can
import cantools
import os
import time
from tqdm import tqdm
import usb

import argparse
import json

CONFIG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'dashboard.json'))

class CANBus:
    def __init__(self, firmware_base='', verbose=False, use_socket=False):
        if (not firmware_base):
            config = json.load(open(CONFIG_FILE_PATH))
            firmware_base = config['firmware_path']
        dbc_path = os.path.join(firmware_base, 'common/daq/per_dbc.dbc')
        db = cantools.database.load_file(dbc_path)
        self.db = db
        self.bus = None
        self.verbose = verbose
        self.use_socket = use_socket
        self.logfn = print

    def connect_gsusb(self):
        dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
        bus = None
        if dev:
            channel = dev.product
            bus_num = dev.bus
            addr = dev.address
            del(dev)
            bus = can.ThreadSafeBus(bustype="gs_usb", channel=channel, bus=bus_num, address=addr, bitrate=500000, receive_own_messages=True)
            while(bus.recv(0)): pass
        else:
            raise RuntimeError("failed to connect to gsusb")
        self.bus = bus
        self._logInfo("connected to gs_usb can")
        atexit.register(self.disconnect)

    def connect_socket(self):
        # https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html
        # sudo ip link set can0 up type can bitrate 500000
        bus = can.ThreadSafeBus(channel='can0', interface='socketcan', bitrate=500000, receive_own_messages=True)
        while(bus.recv(0)): pass
        self.bus = bus
        self._logInfo("connected to socketcan")
        atexit.register(self.disconnect)

    def disconnect_gsusb(self):
        self.bus.shutdown()
        usb.util.dispose_resources(self.bus.gs_usb.gs_usb)
        del(self.bus)
        self.bus = None
        self._logInfo("disconnected from usb")

    def disconnect_socket(self):
        self.bus.shutdown()
        del(self.bus)
        self.bus = None
        self._logInfo("disconnected from socketcan")

    def connect(self):
        if self.use_socket: # (bug in candlelight fw)
            self.connect_socket()
        else:
            self.connect_gsusb()

    def disconnect(self):
        if self.use_socket:
            self.disconnect_socket()
        else:
            self.disconnect_gsusb()
        atexit.unregister(self.disconnect)

    def _logInfo(self, x):  # for compat
        self.logfn(f"LOG: {x}")

    # used to search for TX ack on RX line
    def recv_tx(self, aid, timeout=3.0):
        start = time.time()
        time_left = timeout

        while True:
            # try to get a message
            msg, already_filtered = self.bus._recv_internal(timeout=time_left)

            if (msg and self.verbose):
                print(msg, hex(msg.arbitration_id), hex(aid))
            # could be both 0x404e23c or 0x409c43e (if error frame was echoed back)
            if (msg and (msg.arbitration_id == aid)):
                return msg

            # if not, and timeout is None, try indefinitely
            elif not timeout:
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time.time() - start)

                if time_left > 0:
                    continue

                return None

    def _send_msg(self, msg: can.Message):
        """ Sends a can message over the bus """
        if self.connected():
            #self._logInfo(f"TX: {self.tx_count:03d}: {msg}")
            self.bus.send(msg)
            # CAN sends TX on RX line after arbitration. If we don't ack this the bus gets clogged and we can't send more messages. So find the same message on the RX line and ack it
            # Timestamp:        0.000000    ID: 0409c43e    X Rx                DL:  5    03 9c b2 92 ac
            # Timestamp:        4.830460    ID: 0409c43e    X Tx                DL:  5    03 9c b2 92 ac              Channel: canable gs_usb
            #assert(msg.data == msg2.data) # TODO better way to check this
            msg2 = self.recv_tx(aid=msg.arbitration_id)
            return msg2 and (msg.arbitration_id == msg2.arbitration_id)
        else:
            self._logInfo("Tried to send msg without connection")
            return False

    def drain_messages(self):
        while(self.bus.recv(0)): pass  # drain old messages

    def connected(self):
        return self.bus

    def send_msg(self, msg):
        if not self._send_msg(msg):
            raise RuntimeError(f"failed to TX {msg}")

    # find msg on RX line that matches RX_MSG's aid and cmd id
    def receive_msg(self, RX_MSG, timeout=5.0):
        start = time.time()
        time_left = timeout

        while True:
            # try to get a message
            msg, already_filtered = self.bus._recv_internal(timeout=time_left)

            if (msg and self.verbose):
                print(msg, hex(msg.arbitration_id))

            # return it, if it matches
            if (msg and (msg.arbitration_id == RX_MSG.frame_id)):
                can_rx = RX_MSG.decode(msg.data)
                return can_rx
                #can_rx = RX_MSG.decode(msg.data)
                #if (can_rx['cmd'] == cmd):
                #    return can_rx

            # if not, and timeout is None, try indefinitely
            elif not timeout:
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time.time() - start)

                if time_left > 0:
                    continue
                return None
