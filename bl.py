import atexit
import can
import cantools
from intelhex import IntelHex
import math
import os
import time
from tqdm import tqdm
import usb

from accessory_widgets.bootloader.bootloader_commands import *

import argparse
import json

BOOTLOADER_TIMEOUT = 5.0
CONFIG_FILE_PATH = os.path.join(os.getcwd(), "dashboard.json")

class CANBus:
    def __init__(self, config, verbose=False):
        firmware_base = config['firmware_path']
        dbc_path = os.path.join(firmware_base, 'common/daq/per_dbc.dbc')
        db = cantools.database.load_file(dbc_path)
        self.db = db
        self.bus = None
        self.verbose = verbose

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

    def _logInfo(self, x):  # for compat
        print(f"LOG: {x}")

    # used to search for TX ack on RX line
    def recv_tx(self, aid, timeout=BOOTLOADER_TIMEOUT):
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

class CANBootloader:
    def __init__(self, canbus, node, verbose=False, dry_run=False, use_socket=False):
        self.canbus = canbus
        self.db = self.canbus.db
        self.selected_node = node
        self.bl = BootloaderCommand(self.selected_node, self.db)
        self.verbose = verbose
        self.dry_run = dry_run
        self.use_socket = use_socket

    def _logInfo(self, x): # for compat
        print(f"LOG: {x}")

    def send_msg(self, msg):
        if not self.canbus._send_msg(msg):
            self._logInfo(f"failed to TX {msg}")
            return False
        return True

    # find msg on RX line that matches aid and cmd id
    def recv_rx(self, cmd, timeout=BOOTLOADER_TIMEOUT):
        start = time.time()
        time_left = timeout

        while True:
            # try to get a message
            msg, already_filtered = self.canbus.bus._recv_internal(timeout=time_left)

            if (msg and self.verbose):
                print(msg, hex(msg.arbitration_id))

            # return it, if it matches
            if (msg and (msg.arbitration_id == self.bl.RX_MSG.frame_id)):
                can_rx = self.bl.RX_MSG.decode(msg.data)
                if (can_rx['cmd'] == cmd):
                    return can_rx

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

    def verifyHex(self, path):
        if (path != "" and os.path.exists(path)):
            ih = IntelHex()
            ih.fromfile(path, format="hex")
            self.segments = ih.segments()

            fw_size = 0
            fw_binarr = []
            for i,(start_addr, end_addr) in enumerate(self.segments):
                self._logInfo(f"Segment[{i}]: 0x{start_addr:02X} : 0x{end_addr:02X}")
                if (start_addr < 0x8002000):
                    self._logInfo(f"Invalid start address, ensure the hex is of type BL_ and starts at >= 0x8002000")
                    self.segments = None
                    return

                size = end_addr - start_addr
                fw_size += size
                fw_binarr += ih.tobinarray(start=start_addr, size=size)
                fw_binarr += [0] * (size % 8) # align
                segment_size = math.ceil(fw_size / 8) # sliding window

            self.total_double_words = math.ceil(fw_size / 8)
            self.total_bytes = fw_size
            self.fw_binarr = fw_binarr
            # calc flash delete size (end-start) from 0x8002000
            self.fw_total_padded_size = self.segments[-1][1] - self.segments[0][0]

        else:
            self._logInfo(f"file at {path} not found")

    def fmt_can_rx(self, can_rx):
        key = list(self.bl.RX_CMD.keys())[list(self.bl.RX_CMD.values()).index(can_rx['cmd'])]
        return f"CMD: {key} DATA: 0x{can_rx['data']:x}"

    def flash_firmware(self, path):
        if (not self.canbus.connected()):
            self._logInfo(f"not connected to bus")
            return
        self.canbus.drain_messages()

        self.verifyHex(path)
        if (not self.segments):
            self._logInfo(f"Cannot flash {self.selected_node}, invalid hex")
            return

        flash_start_time = time.time()
        self._logInfo(f"flashing node {self.selected_node}")

        # Stage 1: BLSTAT_WAIT
        # Stage 2: BLSTAT_METDATA_RX
        # Stage 3: BLSTAT_DONE

        # ---------------------------------------------------------
        # stage 1: send reset message
        # BLCMD_RST: resets reset reason & NVIC_SystemReset()
        # returns elapsed time as handshake (no magic)
        self._logInfo("Stage 1: Sending firmware reset message")
        msg = self.bl.firmware_rst_msg()
        if not self.send_msg(msg): return

        # stage1 handshake
        can_rx = self.recv_rx(cmd=self.bl.RX_CMD["BLSTAT_WAIT"])
        if (not can_rx):
            self._logInfo("Stage 1: failed to receive handshake message")
            return
        self._logInfo(f"Stage 1: received handshake; elapsed time: {can_rx['data']} ms")
        if (self.dry_run): # dont erase flash
            return

        msg = self.bl.firmware_size_msg(self.total_double_words * 2)
        if not self.send_msg(msg): return

        # ---------------------------------------------------------
        # stage 2: erase flash
        # BLCMD_ERASE_FLASH: erase total firmware region (end-start) in words starting from start address (0x8002000) configured at init

        self._logInfo(f"Stage 2: Erasing flash region: 0x{self.segments[0][0]:08x} - 0x{self.segments[-1][1]:08x} size: 0x{self.fw_total_padded_size:x}")
        words = math.ceil(self.fw_total_padded_size / 8) * 2  # num words
        msg = self.bl.firmware_start_msg(words) # words
        if not self.send_msg(msg): return

        # stage 2 handshake
        can_rx = self.recv_rx(cmd=self.bl.RX_CMD["BLSTAT_METDATA_RX"])
        if (not can_rx):
            self._logInfo("Stage 2: failed to receive handshake message")
            return
        self._logInfo(f"Stage 2: received handshake; successfully erased flash; magic: 0x{can_rx['data']:x}")

        # ---------------------------------------------------------
        # stage 3: configure firmware size
        # check can_rx['data'] for some checksum
        # BLCMD_SET_SIZE: set flash size (total # of words to be sent)

        # ---------------------------------------------------------
        # stage 3: send data stream

        self._logInfo(f"Stage 3: Sending file: {path}")
        self._logInfo(f"Stage 3: File size: 0x{self.total_bytes:x} double words: {math.ceil(self.total_bytes / 8)}")

        crc = 0xFFFFFFFF
        curr_count = 0
        for i,seg in enumerate(self.segments):
            start_addr, end_addr = seg
            size = end_addr - start_addr
            wc = math.ceil(size / 8)

            self._logInfo(f"address change: 0x{start_addr:x} size: {size:x} word: {curr_count:d}")
            msg = self.bl.firmware_addr_msg(start_addr)
            if not self.send_msg(msg): return  # TODO flash cleanup
            time.sleep(0.01)

            self._logInfo("seg[%d]: 0x%08x-0x%08x: streaming: 0x%x bytes wc: %d" % (i, start_addr, end_addr, size, wc))
            for j in tqdm(range(wc)):
                crc = self.send_double_crc32(crc, curr_count)
                curr_count += 1
        assert(curr_count == self.total_double_words)

        # ---------------------------------------------------------
        # stage 4: send checksum

        self._logInfo("Sending CRC checksum")
        msg = self.bl.firmware_crc_msg(crc & 0xFFFFFFFF)
        if not self.send_msg(msg): return

        can_rx = self.recv_rx(cmd=self.bl.RX_CMD["BLSTAT_DONE"])
        if (not can_rx):
            self._logInfo("Stage 4: failed to receive handshake")
            return

        self._logInfo("Firmware send successful, CRC matched")
        self._logInfo("Total time: %.2f seconds" % (time.time() - flash_start_time))

    def send_double_crc32(self, crc, n):
        # packing a 64 bit can data field with two crc32s
        bin_arr = self.fw_binarr[n*8:n*8+4]
        data1 = sum([x << ((i*8)) for i, x in enumerate(bin_arr)])
        crc = self.crc_update(data1, crc)

        bin_arr = self.fw_binarr[n*8+4:n*8+4+4]
        data2 = sum([x << ((i*8)) for i, x in enumerate(bin_arr)])
        crc = self.crc_update(data2, crc)

        can_tx = self.bl.firmware_data_msg((data2 << 32) | data1)
        self.send_msg(can_tx)
        return crc

    # CRC-32b calculation
    def crc_update(self, data, prev):
        crc = prev ^ data
        idx = 0
        while (idx < 32):
            if (crc & 0x80000000): crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
            else: crc = (crc << 1) & 0xFFFFFFFF
            idx += 1
        return crc

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument("-p", "--path", default="",
        help="path to .hex file to flash",
    )
    parser.add_argument('-t', "--test", action='store_true',
        help="run unit test",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-d', "--dry-run", action='store_true',
        help="dry run (dont erase flash)",
    )
    parser.add_argument('-s', "--socket", action='store_true',
        help="use linux socket backend instead of gs_usb (linux only)",
    )

    args = parser.parse_args()
    config = json.load(open(CONFIG_FILE_PATH))
    node = args.node
    path = os.path.join(config['firmware_path'], "output", node, f"BL_{node}.hex") if not args.path else args.path
    #path = "/home/eileen/per/firmware/output/main_module/BL_main_module.hex"

    canbus = CANBus(config, verbose=args.verbose)
    canbus.connect()

    cb = CANBootloader(canbus, node=node, verbose=args.verbose, dry_run=args.dry_run, use_socket=args.socket)
    if (not args.test):
        cb.flash_firmware(path)
    else:
        for n in range(10):
            cb.flash_firmware(path)
            time.sleep(1) # wait 3s to enter bootloader mode again
