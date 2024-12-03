
import argparse
import can
from canbus import CANBus
import os
import math
from intelhex import IntelHex
from tqdm import tqdm
import time
import json

BLSTAT_VALID        = 0
BLSTAT_INVALID      = 1
BLSTAT_INVALID_CRC  = 2
BLSTAT_UNKNOWN_CMD  = 3

BLCMD_START = 0x1 # /* Request to start firmware download */
BLCMD_CRC_BACKUP = 0x2   #     /* Final CRC-32b check of firmware */
BLCMD_CRC = 0x3     #     /* Final CRC-32b check of firmware */
BLCMD_JUMP = 0x4   #  /* Request for reset */
BLCMD_RST = 0x5    #  /* Request for reset */

CONFIG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'dashboard.json'))

# CRC-32b calculation
def crc_update(data, prev):
    crc = prev ^ data
    idx = 0
    while (idx < 32):
        if (crc & 0x80000000): crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
        else: crc = (crc << 1) & 0xFFFFFFFF
        idx += 1
    return crc

def firmware_flash(canbus, node, path):
    txmsg = canbus.db.get_message_by_name(f"{node}_bl_cmd")
    rxmsg = canbus.db.get_message_by_name(f"{node}_bl_resp")
    bsmsg = canbus.db.get_message_by_name(f"bitstream_data")

    ih = IntelHex()
    ih.fromfile(path, format="hex")
    segments = ih.segments()

    for i,(start_addr, end_addr) in enumerate(segments):
        print(f"Segment[{i}]: 0x{start_addr:02X} : 0x{end_addr:02X}")
        if (start_addr < 0x8002000):
            raise RuntimeError(f"Invalid start address, ensure the hex is of type BL_ and starts at >= 0x8002000")

    fw_total_padded_size = segments[-1][1] - segments[0][0]
    print(f"fw_total_padded_size: 0x{fw_total_padded_size:X}")
    fw_binarr = ih.tobinarray(start=segments[0][0], size=fw_total_padded_size)
    assert(fw_total_padded_size == len(fw_binarr))
    assert(len(fw_binarr) % 4 == 0)

    tick = time.time()

    # 1. enter bootloader mode
    data = txmsg.encode({"cmd": BLCMD_RST, "data": fw_total_padded_size})
    msg = can.Message(arbitration_id=txmsg.frame_id, data=data)
    canbus.send_msg(msg)
    #msg = canbus.receive_msg(rxmsg) # TODO boot status message
    #print(msg)
    tock = time.time()
    print(tock - tick)

    # 2. erase flash
    data = txmsg.encode({"cmd": BLCMD_START, "data": fw_total_padded_size})
    msg = can.Message(arbitration_id=txmsg.frame_id, data=data)
    canbus.send_msg(msg)
    msg = canbus.receive_msg(rxmsg)
    print(msg)
    assert(msg['cmd'] == BLSTAT_VALID and msg['data'] == fw_total_padded_size)
    tock = time.time()
    print(tock - tick)  # 4.161547660827637

    # 3. send data
    crc = 0xFFFFFFFF
    for i in range(len(fw_binarr) // 4):
        x = fw_binarr[i*4:(i+1)*4]
        payload = sum([y << ((i*8)) for i,y in enumerate(x)])
        #payload = x[3] << 24 | x[2] << 16 | x[1] << 8 | x[0]
        data = payload << 16 | i & 0xffff
        msg = can.Message(arbitration_id=bsmsg.frame_id, data=data.to_bytes(8, 'little'))
        canbus.send_msg(msg)
        #msg = canbus.receive_msg(rxmsg)
        #print(msg)
        crc = crc_update(payload, crc)
    print(hex(crc))
    tock = time.time()
    print(tock - tick) # 6.891172885894775

    # 4. send CRC
    data = txmsg.encode({"cmd": BLCMD_CRC, "data": crc})
    msg = can.Message(arbitration_id=txmsg.frame_id, data=data)
    canbus.send_msg(msg)
    msg = canbus.receive_msg(rxmsg, timeout=15.0)
    print(msg)
    assert(msg['cmd'] == BLSTAT_VALID and msg['data'] == crc)
    tock = time.time()
    print(tock - tick)  # 8.122606992721558

    # 5. jump
    data = txmsg.encode({"cmd": BLCMD_JUMP, "data": 0})
    msg = can.Message(arbitration_id=txmsg.frame_id, data=data)
    canbus.send_msg(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-s', "--socket", action='store_true',
        help="use linux socket backend instead of gs_usb (linux only)",
    )

    args = parser.parse_args()
    node = args.node
    config = json.load(open(CONFIG_FILE_PATH))
    node = args.node
    path = os.path.join(config['firmware_path'], "output", node, f"BL_{node}.hex") if not args.path else args.path
    #path = "/home/eileen/per/firmware/output/main_module/BL_main_module.hex"
    #path = f"/home/eileen/per/firmware/output/{node}/BL_{node}.hex"
    if (not (path and os.path.exists(path))):
        raise RuntimeError("Invalid firmware path: %s" % (path))

    canbus = CANBus(verbose=args.verbose, use_socket=args.socket)
    canbus.connect()
    firmware_flash(canbus, node, path)
