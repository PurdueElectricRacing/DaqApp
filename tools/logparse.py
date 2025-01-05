#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# Parse raw binary CAN ringbuffer files from DAQ

from communication.common import *

from termcolor import colored
import can
import cantools
import argparse
import os
import datetime

class DAQCANFrame:
    def __init__(self, rawbytes):
        self.db = cantools.db.load_file("/home/eileen/per/firmware/common/daq/per_dbc.dbc")
        # DAQ Frame bytes to can.Message object
        frame = DAQFrameStruct.parse(rawbytes)
        assert(frame.frame_type in [DAQ_FRAME_CAN_RX, DAQ_FRAME_TCP2CAN, DAQ_FRAME_TCP2UDS])
        assert(frame.bus_id in [DAQ_FRAME_BUSID_CAN1, DAQ_FRAME_BUSID_CAN2])
        assert(frame.dlc > 0 and frame.dlc <= 8)

        self.frame_type = frame.frame_type
        self.tick_ms = frame.tick_ms
        self._can_id = frame.msg_id
        self.bus_id = frame.bus_id
        self.dlc = frame.dlc
        self.data = frame.data
        self.arb_id = self.parse_canid(frame.msg_id)

        self.can_msg = self.frame2message(self)
        if (self.can_msg.is_error_frame):
            pass
        else:
            self.dbc_msg = self.db.get_message_by_frame_id(self.can_msg.arbitration_id)
            self.dec_msg = self.dbc_msg.decode(self.can_msg.data)

    def parse_canid(self, can_id):
        # decompose ID
        is_extended = bool(can_id & CAN_EFF_FLAG)
        if is_extended:
            arb_id = can_id & 0x1FFFFFFF
        else:
            arb_id = can_id & 0x000007FF
        return arb_id

    def get_frame_type_str(self, x):
        return dict({DAQ_FRAME_CAN_RX: "CAN", DAQ_FRAME_TCP2CAN: "TCP"})[x]

    def get_bus_str(self, x):
        return dict({DAQ_FRAME_BUSID_CAN1: "CAN1", DAQ_FRAME_BUSID_CAN2: "CAN2"})[x]

    def _getcolor(self):
        colors = ['green', 'yellow', 'magenta', 'cyan', 'white']
        color = (self.arb_id << 8) % len(colors)
        return colors[color]

    def get_id_str(self, x):
        s = colored('{:08x}'.format(x), self._getcolor())
        #s = "0" * (8 - len('{:x}'.format(x))) + s
        return s

    def get_hex_str(self, x):
        s = '{:02x}'.format(x)
        if (x):
            #colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
            colors = ['red', 'green', 'yellow', 'magenta', 'cyan']
            s = colored(s, colors[x % len(colors)])
        return s

    def get_data_str(self, data):
        return ' '.join(self.get_hex_str(x) for x in data)

    def get_sender_str(self):
        x = self.dbc_msg.senders[0]
        if (x == "Main_Module"):
            x = "Main"
        return x

    def get_msg_name_str(self):
        return colored(self.dbc_msg.name, self._getcolor())

    def __repr__(self):
        s = f"  Frame:"
        #s += " src: {self.get_frame_type_str(self.frame_type)}"
        s += f" ID: {self.get_id_str(self.arb_id)} |"
        s += f" {self.tick_ms/1000.0:8.04f} |"
        s += f" TX: {self.get_sender_str()} |"
        s += f" DL: {int(self.dlc)} |"
        s += f" {self.get_data_str(self.data)} |"
        s += f" {self.get_msg_name_str()}"
        #s += f"  "
        #s += f" {self.get_sender_str()} |"
        #s += f" {self.dbc_msg.name}\n"
        return s

    def frame2message(self, frame):
        return can.Message(
            timestamp = frame.tick_ms / 1000.0,
            arbitration_id = frame.arb_id,
            is_extended_id = bool(frame._can_id & CAN_EFF_FLAG),
            is_error_frame = bool(frame._can_id & CAN_ERR_FLAG),
            is_remote_frame = bool(frame._can_id & CAN_RTR_FLAG),
            dlc=frame.dlc,
            channel=frame.bus_id,
            data=frame.data,
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', "--number", default=0, type=int,
        help="count, default 0 (all)",
    )
    args = parser.parse_args()

    try:
        sd_dir = "/media/eileen/A04D-8962/"
        print(f"Searching log dir {sd_dir}")
        x = list(pathlib.Path(sd_dir).glob('*.log'))
        for path in x:
            t = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M:%S')
            print(f" date: {t} path: {path}")

            data = open(path, "rb").read()
            count = len(data) // DAQ_FRAME_SIZE if (args.number == 0) else args.number
            for n in range(count):
                chunk = data[n*DAQ_FRAME_SIZE:(n+1)*DAQ_FRAME_SIZE]
                frame = DAQCANFrame(chunk)
                if (frame.can_msg.is_error_frame):
                    print("Skipping error frame")
                    continue
                print(frame)
    except KeyboardInterrupt:
        pass
