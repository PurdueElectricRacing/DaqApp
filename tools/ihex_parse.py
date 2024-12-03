from intelhex import IntelHex
import os
import time
import argparse
import json

path = "/home/eileen/per/firmware/output/bootloaders/bootloader_main_module/BL_bootloader_main_module.hex"


ih = IntelHex()
ih.fromfile(path, format="hex")
segments = ih.segments()

for i,(start_addr, end_addr) in enumerate(segments):
    print(f"Segment[{i}]: 0x{start_addr:02X} : 0x{end_addr:02X}")
