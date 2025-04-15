#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import can
from communication.common import DAQAppObject, dotdict, tempdir, cd
from communication.canbus_backend import CANBusUSB, CANBusTCP
import os
import math
from intelhex import IntelHex
from tqdm import tqdm
import time
import json
import random

import tarfile
import subprocess

BLCMD_PING      = 0x00
BLCMD_START     = 0x01
BLCMD_CRC       = 0x02
BLCMD_DATA      = 0x03
BLCMD_RST       = 0x05

BLCMD_STAT      = 0x08
BLCMD_BACKUP    = 0x09

BLERROR_NONE  = 0
BLERROR_CRC   = 1
BLERROR_FLASH = 2
BLERROR_SIZE  = 3
BLERROR_META  = 4
BLERROR_UNKNOWN = 5

BLSTAT_VALID        = 0
BLSTAT_BOOT         = 4

BL_BANK_A = 0xAAAA
BL_BANK_B = 0xBBBB
BL_BANK_C = 0xCCCC

BL_METADATA_MAGIC = 0xFEE1DEAD
BL_PING_MAGIC     = 0xFEE2DEAD
BL_FIRMWARE_NOT_VERIFIED = 0xffffffff
BL_FIRMWARE_VERIFIED     = 0x00000000

NODES = ["a_box", "daq", "dashboard", "main_module", "pdu"]

class BootloaderMessage(dotdict):
    def check_response(self, cmd, data=0):
        #if ((data and self.data != data)):
        if ((self.cmd != cmd) or (data and self.data != data)):
            print(f"ERR: msg: {self}")
            raise ValueError("Failed to check response")
        return
        if (self.err != BLERROR_NONE):
            print(f"ERR: msg: {self} reason: {self.err} ({self._get_err_str(self.err)})")
            raise ValueError("Failed to check response")
        assert(self.err == BLERROR_NONE)
        if ((self.cmd != cmd) or (data and self.data != data)):
            print(f"ERR: msg: {self}")
            raise ValueError("Failed to check response")

    def _get_err_str(self, e):
        return {BLERROR_NONE:"BLERROR_NONE", BLERROR_CRC:"BLERROR_CRC", BLERROR_FLASH:"BLERROR_FLASH", BLERROR_SIZE:"BLERROR_SIZE", BLERROR_META:"BLERROR_META", BLERROR_UNKNOWN:"BLERROR_UNKNOWN"}[e]

    def __repr__(self):
        s = f"BL Message: cmd: 0x{self.cmd:02x} data: 0x{self.data:08x}"
        return s

class Bootloader(DAQAppObject):
    def __init__(self, canbus, verbose=False):
        super(Bootloader, self).__init__(verbose)
        self.canbus = canbus

    # CRC-32b calculation
    def crc_update(self, data, prev):
        crc = prev ^ data
        idx = 0
        while (idx < 32):
            if (crc & 0x80000000): crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
            else: crc = (crc << 1) & 0xFFFFFFFF
            idx += 1
        return crc

    def receive(self, node, cmd, **kwargs):
        canbus = self.canbus
        msg = canbus.receive_uds_frame(node=node, cmd=cmd, **kwargs)
        blmsg = BootloaderMessage({"cmd":msg.cmd, "err": msg.data & 0xff, "data":msg.data >> 8, "data_raw":msg.data})
        return blmsg

    def reset_node(self, node, args):
        canbus = self.canbus
        canbus.send_uds_frame(node=node, cmd=BLCMD_RST, data=0)

    def ping(self, node, args):
        canbus = self.canbus
        UDS_CMD_SYS_TEST = 0x06
        x = random.randint(0, 0xffff // 2)
        y = random.randint(0, 0xffff // 2)
        data = (x & 0xffff) | (y & 0xffff) << 16
        canbus.send_uds_frame(node, UDS_CMD_SYS_TEST, data=data)
        msg = canbus.receive_uds_frame(node, UDS_CMD_SYS_TEST, timeout=3.0)
        z = (msg.data >> 32) & 0xffff
        if (x + y != z):
            print(msg, hex(x), hex(y), hex(z))
        assert(x + y == z)
        self.log(f"Ping from {node}! (0x{x:04x} + 0x{y:04x} == 0x{z:04x})")
        return z

    def is_bootloader_loaded(self, node, args):
        canbus = self.canbus
        canbus.send_uds_frame(node, BLCMD_PING, data=0)
        msg = self.receive(node, BLCMD_PING, timeout=1.0)
        if (msg.data == 0xDEADBEEF):
            self.log("Query: Bootloader is NOT loaded")
        elif (msg.data == BL_METADATA_MAGIC):
            self.log("Query: Bootloader is loaded")
        else:
            self.log(str(msg))
            self.log("wtf?")
        return msg.data == BL_METADATA_MAGIC

    def enter_bootloader_mode(self, node, args):
        if (not self.is_bootloader_loaded(node, args)): return False
        # DAQ can do uninterrupted updates but other nodes can't due to psched watchdog (DAQ doesnt use psched)
        # Erasing flash takes minimum 1.5 seconds but psched times out in ~10ms so we can't erase flash within app code. Unfortunately we have to erase flash to write to flash because NOR and we don't have enough RAM
        # So pull NVIC reset to go back to the start of flash and enter "bootloader mode" by literally running the bootloader again lol
        canbus = self.canbus
        if (not args.in_place):
            self.reset_node(node, args)
            msg = self.receive(node, 0, timeout=1.0)
            msg.check_response(0, 0xFEE2DEAD)

        # 1. Ping to enter bootloader mode
        canbus.send_uds_frame(node, cmd=BLCMD_PING, data=0)
        msg = self.receive(node, BLCMD_PING, timeout=1.0)
        print(msg)
        msg.check_response(BLCMD_PING, BL_METADATA_MAGIC)
        if (not args.in_place):
            self.log("Pong! Entered bootloader mode!")
        else:
            self.log("Pong! Entered bootloader mode IN PLACE!")
        return True

    def get_bootstat(self, node, args):
        if (not self.enter_bootloader_mode(node, args)): return False
        # prints contents of metadata bank/bootmanager: addr, words, checksum, verified
        for bank in [BL_BANK_B, BL_BANK_C]:
            canbus.send_uds_frame(node, BLCMD_STAT, data=bank)
            meta = []
            for n in range(4): # 2x: one for main manager, the second for backup manager
                msg = self.receive(node, BLCMD_STAT, timeout=1.0)
                msg.check_response(BLCMD_STAT)
                meta.append(msg.data)
                #print(msg)
            self.log("-"*22)
            self.log(f"Partition: 0x{bank:04X}")
            self.log(f"  Address: 0x{meta[0]:08x}")
            self.log(f"    Words: 0x{meta[1]:04x} (0x{meta[1] << 2:04x} bytes)")
            self.log(f"      CRC: 0x{meta[2]:08x}")
            if meta[3] == BL_FIRMWARE_VERIFIED:
                vs = "Valid, Verified"
            elif meta[3] == BL_FIRMWARE_NOT_VERIFIED:
                vs = "Valid, Unverified"
            else:
                vs = "NULL"
            self.log(f" Verified: 0x{meta[3]:08x} ({vs})")

    def load_backup_firmware(self, node, args):
        if (not self.enter_bootloader_mode(node, args)): return False
        canbus = self.canbus
        canbus.send_uds_frame(node, BLCMD_BACKUP, data=BL_BANK_C)
        msg = self.receive(node, BLCMD_BACKUP, timeout=5.0)
        msg.check_response(BLCMD_BACKUP) # TODO error
        self.log("Configured to load backup firmware on next boot")
        self.log("Resetting to force boot backup firmware...")
        self.reset_node(node, args)

    def flash_firmware(self, node, path, args):
        canbus = self.canbus
        if (not (os.path.exists(path))):
            raise RuntimeError("Firmware does not exist at: %s" % (path))

        ih = IntelHex()
        ih.fromfile(path, format="hex")
        segments = ih.segments()
        self.log(f"Flashing node {node} with firmware {path}")

        for i,(start_addr, end_addr) in enumerate(segments):
            self.log(f"Segment[{i}]: 0x{start_addr:02X} : 0x{end_addr:02X}")
            if (start_addr < 0x8002000):
                raise RuntimeError(f"Invalid start address, ensure the hex is of type BL_ and starts at >= 0x8002000")

        fw_total_padded_size = segments[-1][1] - segments[0][0]
        fw_binarr = ih.tobinarray(start=segments[0][0], size=fw_total_padded_size)
        assert(fw_total_padded_size == len(fw_binarr))
        assert(len(fw_binarr) % 4 == 0)

        tick = time.time()
        # 1. Enter bootloader mode/handshake
        if (not self.enter_bootloader_mode(node, args)): return False
        self.log("Delta: %.4f: Entered bootloader mode" % (time.time()-tick))

        # 2. Erase flash
        wc = fw_total_padded_size // 4
        data = wc & 0xffff | ((0 & 0xffff) << 16)
        canbus.send_uds_frame(node, BLCMD_START, data=data)
        msg = self.receive(node, BLCMD_START, timeout=15.0)
        msg.check_response(BLCMD_START, wc)
        self.log("Delta: %.4f: Erased flash size 0x%x" % (time.time()-tick, wc << 2))

        # 3. Send data
        self.log(f"Delta: {(time.time()-tick):.4f}: Sending over firmware bits...")
        crc = 0xFFFFFFFF
        for i in tqdm(range(wc)):
            x = fw_binarr[i*4:(i+1)*4]
            payload = sum([y << ((i*8)) for i,y in enumerate(x)])
            #payload = x[3] << 24 | x[2] << 16 | x[1] << 8 | x[0]
            data = payload << 16 | i & 0xffff
            try:
                canbus.send_uds_frame(node, BLCMD_DATA, data=data)
                msg = self.receive(node, BLCMD_DATA, timeout=5.0)
                msg.check_response(BLCMD_DATA, 6)
            except TimeoutError:
                self.log("error")
                self.log(i)
                #self.log(msg)
                raise ValueError ("exit")
            crc = self.crc_update(payload, crc)

        self.log("Delta: %.4f: Sending CRC: 0x%08x" % (time.time()-tick, crc))

        # 4. Send CRC
        flags = BL_BANK_C if args.set_backup else BL_BANK_B
        data = (crc & 0xffffffff) | (flags & 0xffff) << 32
        canbus.send_uds_frame(node, BLCMD_CRC, data=data)
        msg = self.receive(node, BLCMD_CRC, timeout=5.0)
        msg.check_response(BLCMD_CRC, crc)
        self.log("Delta: %.4f: Verified CRC checksum 0x%x" % (time.time()-tick, crc))

    def download(self, node, args):
        if (not self.enter_bootloader_mode(node, args)): return False
        tick = time.time()
        flags = BL_BANK_C if args.set_backup else BL_BANK_A  # B moves to A after boot
        canbus.send_uds_frame(node, BLCMD_DOWNLOAD, data=flags)
        msg = self.receive(node, BLCMD_DOWNLOAD, timeout=5.0)
        msg.check_response(BLCMD_DOWNLOAD)
        wc = msg.data & 0xffff
        crc_bl = (msg.data >> 16) & 0xffffffff
        assert(wc and crc_bl)
        self.log(f"Delta: {time.time()-tick:.4f}: Found firmware: hash: {crc_bl:08x} size: 0x{wc << 2:x}")
        self.log(f"Delta: {time.time()-tick:.4f}: Downloading firmware {crc_bl:08x}...")

        firmware = []
        crc = 0xFFFFFFFF
        for i in tqdm(range(wc)):
            msg = self.receive(node, BLCMD_DOWNLOAD, timeout=5.0)
            msg.check_response(BLCMD_DOWNLOAD)
            payload = msg.data
            crc = self.crc_update(payload, crc)
            firmware.append(payload)
        assert(crc == crc_bl)
        #firmware = struct.pack("<%dI" % (len(firmware)), *firmware)
        self.log(f"Delta: {time.time()-tick:.4f}: CRC matched! firmware {crc:08x} download success!")

    def is_firmware_package(self, path):
        return (path.endswith('.tar.gz'))

    def flash_firmware_package(self, tarball_path, args):
        if not (self.is_firmware_package(tarball_path)):
            self.log(f"ERR: {tarball_path} is not firmware package")
            return
        self.log(f"Firmware package path: {tarball_path}")
        with tempdir() as dirpath:
            subprocess.run([f"cp {tarball_path} ."], shell=True)
            print(os.path.basename(tarball_path))
            subprocess.run([f"tar -xzvf {os.path.join(dirpath, os.path.basename(tarball_path))}"], shell=True)
            print(os.listdir())
            for entry in os.scandir('.'):
                if entry.is_file():
                    print(entry.name)
            #tar = tarfile.open(os.path.join(os.curdir, tarball_path), "r:gz")
            #tar.extractall()
            #tar.close()
            print(os.listdir())
            for node in NODES:
                print(node)
                path = os.path.join(os.path.abspath(os.curdir), f"output/{node}/BL_{node}.hex")
                print(path)
                if (node in ["a_box", "torque_vector", "dashboard"]): continue
                self.flash_firmware(node, path, args)

def map_node_names(name):
    name = name.lower()
    if (name == "main"): return "main_module"
    return name

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
        help="Node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="Verbose",
    )
    parser.add_argument("--path", default='',
        help="Path to firmware",
    )
    parser.add_argument('-m', "--mode", default='usb',
        help="USB/TCP",
    )
    parser.add_argument('-b', "--set-backup", action='store_true',
        help="Flash firmware as backup firmware",
    )
    parser.add_argument('-s', "--stat", action='store_true',
        help="Print boot stat",
    )
    parser.add_argument('-l', "--load-backup", action='store_true',
        help="Load backup firmware from storage",
    )
    parser.add_argument('-r', "--reset", action='store_true',
        help="Pull NVIC hard reset",
    )
    parser.add_argument('-p', "--ping", action='store_true',
        help="ping!",
    )
    parser.add_argument('-i', "--in-place", action='store_true',
        help="in place updates, i.e. dont pull reset",
    )
    parser.add_argument('-d', "--download", action='store_true',
        help="in place updates, i.e. dont pull reset",
    )

    args = parser.parse_args()
    CONFIG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'dashboard.json'))
    config = json.load(open(CONFIG_FILE_PATH))
    node = map_node_names(args.node)

    path = os.path.join(config['firmware_path'], "output", node, f"BL_{node}.hex") if not args.path else args.path
    #if (args.set_backup):
    #    path = "/home/eileen/per/data/BL_main_module_backup.hex"
    #path = "/home/eileen/per/firmware/output/main_module/BL_main_module.hex"
    #path = f"/home/eileen/per/firmware/output/{node}/BL_{node}.hex"
    #path = "/home/eileen/per/firmware/output/firmware-backup-2025-02-12-66ffd0b3.tar.gz"
    #path = "/home/eileen/per/firmware/output/firmware-2025-03-08-86aa21e8.tar.gz"
    if (not (os.path.exists(path))):
        raise RuntimeError("Invalid firmware path: %s" % (path))

    if (args.mode == "tcp"):
        canbus = CANBusTCP(None, verbose=args.verbose)
        canbus.connect()
    else:
        canbus = CANBusUSB(None, verbose=args.verbose)
        canbus.connect(use_gsusb=False) # socketcan tx queue limit?
    assert(canbus.connected())
    canbus.start_thread()

    bl = Bootloader(canbus)
    if (args.reset):
        bl.reset_node(node, args)
    elif (args.download):
        bl.download(node, args)
    elif (args.ping):
        bl.ping(node, args)
    elif (args.stat):
        bl.get_bootstat(node, args)
    elif (args.load_backup):
        bl.load_backup_firmware(node, args)
    else:
        if (bl.is_firmware_package(path)):
            bl.flash_firmware_package(path, args)
        else:
            bl.flash_firmware(node, path, args)

    canbus.stop_thread()
