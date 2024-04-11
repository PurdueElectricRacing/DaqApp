import os
import cantools
import can
import numpy as np
import math
from matplotlib import pyplot as plt

# Logging helper functions
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_error(phrase):
    print(f"{bcolors.FAIL}ERROR: {phrase}{bcolors.ENDC}")

def log_warning(phrase):
    log(f"{bcolors.WARNING}WARNING: {phrase}{bcolors.ENDC}")

def log_success(phrase):
    log(f"{bcolors.OKGREEN}{phrase}{bcolors.ENDC}")

def log(phrase):
    print(phrase) 

class BusLoad():
    """
    Exports a binary log files into csv files
    Separate CSV files are created based on groupings 
        of continuous time intervals
    """
    CAN_EFF_FLAG = 0x80000000
    CAN_RTR_FLAG = 0x40000000
    CAN_ERR_FLAG = 0x20000000
    MSG_BYTE_LEN = 18
    MAX_JUMP_MS = 300 # Creates new file if message is this far from previous

    def __init__(self):

        self.start_t = 0
        self.start_t_valid = False
        self.out_file = None

    def _bytes_to_message(self,b:bytearray):
        """Convert raw bytes to can.Message object"""
        ts = int.from_bytes(b[:4], "little")/1000.0
        can_id = int.from_bytes(b[4:8], 'little')
        bus_id = b[8]
        dlc = b[9]
        #decompose ID
        is_extended = bool(can_id & self.CAN_EFF_FLAG) #CAN_EFF_FLAG
        if is_extended:
            arb_id = can_id & 0x1FFFFFFF
        else:
            arb_id = can_id & 0x000007FF

        return can.Message(
            timestamp = ts,
            arbitration_id = arb_id,
            is_extended_id = is_extended,
            is_error_frame = bool(can_id & self.CAN_ERR_FLAG),
            is_remote_frame = bool(can_id & self.CAN_RTR_FLAG),
            dlc=dlc,
            channel=bus_id,
            data=b[10:10+dlc]
        )

    def _get_input_file_list(self, dir):
        "Gets .log files sorted by creation time"
        def get_creation_time(item):
            item_path = os.path.join(dir, item)
            return os.path.getctime(item_path)
        items = [i for i in os.listdir(dir) if i.endswith('.log')]
        sorted_items = sorted(items, key=get_creation_time)
        return sorted_items

    WINDOW_WIDTH_S = 1.0
    BIN_WIDTH_S = 0.005
    BUS_RATE = 500000

    def parse_files(self, input_dir, bus='Main'):
        # Determine files in directory of type .log        
        # The created file should contain info about which log files it contains

        in_logs = self._get_input_file_list(input_dir)

        # Create the row to write for each bin

        last_t = 0
        t_gap = True

        # Iterate through all messages in all input files
        for in_log in in_logs:
            print(in_log)
            if t_gap:
                last_t = 0
                self.bins = np.zeros(math.floor(self.WINDOW_WIDTH_S / self.BIN_WIDTH_S))
                self.t = np.arange(0.0, self.WINDOW_WIDTH_S, self.BIN_WIDTH_S)
                self.start_t = 0
                self.start_t_valid = False
                t_gap = False

            with open(os.path.join(input_dir, in_log), 'rb') as f:
                while True:
                    s = f.read(self.MSG_BYTE_LEN)
                    if len(s) == 0: break
                    ba = bytearray(s)
                    msg = self._bytes_to_message(ba)

                    # Determine time delta
                    if not self.start_t_valid:
                        self.start_t = msg.timestamp
                        self.start_t_valid = True
                        print(f"Set start: {self.start_t}")
                    else:
                        if (msg.timestamp - last_t < 0 or msg.timestamp - last_t > 1):
                            print(f"time gap, stopping: {last_t}")
                            print(f"Duration: {(last_t - self.start_t) / 60} minutes")
                            t_gap = True
                            break
                    t = msg.timestamp - self.start_t

                    # if (0.19 < t < 0.2):
                    #     print(msg)

                    last_t = msg.timestamp
                    
                    idx = math.floor((t % self.WINDOW_WIDTH_S) * 1000) // round(self.BIN_WIDTH_S * 1000)

                    msg_len = 0
                    if msg.is_extended_id:
                        msg_len = 64 + 8 * msg.dlc
                    else:
                        msg_len = 44 + 8 * msg.dlc
                    
                    self.bins[idx] = self.bins[idx] + msg_len
                if t_gap:
                    iteration_count = math.floor(((last_t - self.start_t) / self.WINDOW_WIDTH_S))
                    bits_per_bin = round(self.BIN_WIDTH_S * self.BUS_RATE)
                    self.bins = self.bins / iteration_count / bits_per_bin * 100
                    plt.bar(self.t, self.bins, width=self.BIN_WIDTH_S)
                    plt.show()
        


#p = "D:/log_recovery/recovered_logs/"
p = "F:/"
#p = "D:/Otterbein_4_5_24/input_load"
#p = "D:/2024_04_01_logs/in"
#p = "D:/log_recovery/test_in" 
#p = "D:/log_recovery/ruhaan_driving/"
#out_dir = "D:/log_recovery/test_out"
#out_dir = "D:/2024_04_01_logs/out"

#dbc_dir = "D:/Downloads/per_dbc.dbc"
dbc_dir = "C:/users/lukeo/Documents/firmware/common/daq/per_dbc.dbc"

le = BusLoad()

le.parse_files(p)
