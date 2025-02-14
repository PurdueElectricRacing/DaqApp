from intelhex import IntelHex
import os
import time
import argparse
import json

def crc_update(data, prev):
    crc = prev ^ data
    idx = 0
    while (idx < 32):
        if (crc & 0x80000000): crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
        else: crc = (crc << 1) & 0xFFFFFFFF
        idx += 1
    return crc

node = "torque_vector"
path = f"/home/eileen/per/firmware/output/bootloaders/bootloader_{node}/BL_bootloader_{node}.hex"
path = f"/home/eileen/per/firmware/output/{node}/BL_{node}.hex"
print(path)

ih = IntelHex()
ih.fromfile(path, format="hex")
segments = ih.segments()

for i,(start_addr, end_addr) in enumerate(segments):
    print(f"Segment[{i}]: 0x{start_addr:02X} : 0x{end_addr:02X}")
    fw_binarr = ih.tobinarray(start=start_addr, size=end_addr-start_addr)
    #
    for j in range(4):
        x = fw_binarr[j*4:(j+1)*4]
        payload = sum([y << ((k*8)) for k,y in enumerate(x)])
        print(hex(payload))

fw_total_padded_size = segments[-1][1] - segments[0][0]
print(f"size: 0x{fw_total_padded_size:08x}")
fw_binarr = ih.tobinarray(start=segments[0][0], size=fw_total_padded_size)
crc = 0xffffffff
for i in range(fw_total_padded_size // 4):
    x = fw_binarr[i*4:(i+1)*4]
    payload = sum([y << ((i*8)) for i,y in enumerate(x)])
    crc = crc_update(payload, crc)
print(f"crc: {crc:08x}")
