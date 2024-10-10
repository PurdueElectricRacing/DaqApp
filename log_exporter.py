import os
import cantools
import can
import numpy as np

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

class LogExporter():
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

    def __init__(self, dbc_path):
        self.db = cantools.db.load_file(dbc_path)
        self._init_col_dict()

        self.start_t = 0
        self.start_t_valid = False
        self.out_file = None
        self.prev_is_err = False
        self.prev_msg = ""

        self.out_to_file = True

        np.set_printoptions(nanstr="")

    def _init_col_dict(self):
        # Bus
        # Node
        # Message
        # Signal
        # dictionary for [bus][node][message][signal] -> idx
        self.signal_to_col = {}
        col = 1 # start at 1 for time

        bus_row = "Bus"
        node_row ="Node"
        msg_row = "Message"
        sig_row = "Signal"

        for msg_c in self.db.messages:
            bus = msg_c.bus_name
            node = msg_c.senders[0]
            msg = msg_c.name
            if not bus in self.signal_to_col:
                self.signal_to_col[bus] = {}
            if not node in self.signal_to_col[bus]:
                self.signal_to_col[bus][node] = {}

            self.signal_to_col[bus][node][msg] = {}
            for sig in msg_c.signals:
                self.signal_to_col[bus][node][msg][sig.name] = col
                col = col + 1

                # TODO: fill bus name from dbc?
                bus_row += f", {'Main'}"
                node_row += f", {node}"
                msg_row += f", {msg}"
                sig_row += f", {sig.name}"

        self.num_cols = col
        self.header = "\n".join((bus_row, node_row, msg_row, sig_row))
        self.header += '\n'

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

    def _new_out_file(self):
        # Ensure if current row exists that we write it
        if not self.out_to_file: return
        if (self.out_file != None):
            self._write_row()
            self.out_file.close()
        self.out_file = open(os.path.join(self.out_dir, f"out_{self.out_fil_cnt}.csv"), 'w')
        self.out_fil_cnt = self.out_fil_cnt + 1
        self.out_file.write(self.header)
        self.row.fill(np.nan)

    def _write_row(self):
        if not self.out_file: return
        for n in self.row:
            if not np.isnan(n):
                self.out_file.write("%.5f" % n)
            self.out_file.write(',')
        self.out_file.write('\n')
        if not self.fill_empty:
            self.row.fill(np.nan)

    def _update_val(self, t, col, val):
        # Insert value in to current row
        # Write row when necessary

        # Conditions for new file
        if (not self.start_t_valid or
           (t < self.last_t or abs(t - self.last_t) >= self.MAX_JUMP_MS)):
            self.start_time = t
            self.start_t_valid = True
            self.cur_row_t = (int(t * 1000) // self.bin_ms) * self.bin_ms / 1000.0 # floor to bin size
            self._new_out_file()
            self.row[0] = self.cur_row_t

        self.last_t = t

        # Conditions for new row
        if (self.start_t_valid and
           t - self.cur_row_t >= self.bin_ms / 1000.0):
            self._write_row()
            self.cur_row_t += self.bin_ms / 1000.0
            self.row[0] = self.cur_row_t
        if type(val) == float or type(val) == int:
            self.row[col] = val
        else:
            if np.isnan(val.value):
                self.row[col] = ""
            else:
                self.row[col] = val.value

    def _parse_msg(self, msg:can.Message):
        if not msg.is_error_frame:
            dbc_msg = None
            try:
                dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                decode = dbc_msg.decode(msg.data)
                for sig in decode.keys():
                    sig_val = decode[sig]
                    if (type(sig_val) != str):
                        col = self.signal_to_col[dbc_msg.bus_name][dbc_msg.senders[0]][dbc_msg.name][sig]
                        self._update_val(msg.timestamp, col, sig_val)
                # if self.prev_is_err: print(f"{dbc_msg.name} proceeded error")
                #utils.signals[utils.b_str][dbc_msg.senders[0]][dbc_msg.name][sig].update(sig_val, msg.timestamp, not utils.logging_paused or self.is_importing)
                self.prev_msg = dbc_msg.name
            except KeyError:
                if dbc_msg and "daq" not in dbc_msg.name and "fault" not in dbc_msg.name:
                    log_warning(f"Unrecognized signal key for {msg}")
            except ValueError as e:
                if "daq" not in dbc_msg.name:
                    log_warning(f"Failed to convert msg: {msg}")
                    print(e)
        if msg.is_error_frame:
            # log(f"Received error frame: {msg}")
            # if not self.prev_is_err:
            #     print(f"{self.prev_msg} preceeded error")
            self.prev_is_err = True
        else:
            self.prev_is_err = False

    def _get_input_file_list(self, dir):
        "Gets .log files sorted by creation time"
        def get_creation_time(item):
            item_path = os.path.join(dir, item)
            return os.path.getctime(item_path)
        items = [i for i in os.listdir(dir) if i.endswith('.log')]
        sorted_items = sorted(items, key=get_creation_time)
        return sorted_items

    def parse_files(self, input_dir, output_dir, bus='Main', binning_ms=15, fill_empty_vals=True):
        # Determine files in directory of type .log
        # The created file should contain info about which log files it contains
        if (input_dir == output_dir):
            log_error("Input dir == ouput dir!")
            return

        in_logs = self._get_input_file_list(input_dir)

        # Create the row to write for each bin
        self.row = np.empty(self.num_cols)
        self.bin_ms = int(binning_ms)

        # TODO: name the output file...
        self.out_fil_cnt = 0
        self.out_dir = output_dir

        self.fill_empty = fill_empty_vals

        # Iterate through all messages in all input files
        for in_log in in_logs:
            with open(os.path.join(input_dir, in_log), 'rb') as f:
                while True:
                    s = f.read(self.MSG_BYTE_LEN)
                    if len(s) == 0: break
                    ba = bytearray(s)
                    msg = self._bytes_to_message(ba)
                    decode = self._parse_msg(msg)

        if self.out_file != None:
            self.out_file.close()

#p = "D:/log_recovery/recovered_logs/"
p = "F:/"
#p = "D:/2024_04_01_logs/in"
p = "D:/Otterbein_04_06_2024/Evening"
p = "C:/Users/Ruhaan Joshi/Downloads/log-2024-02-27--23-15-02"
p = "/media/eileen/A04D-8962"
#p = "D:/log_recovery/test_in"
#p = "D:/log_recovery/ruhaan_driving/"
#out_dir = "D:/log_recovery/test_out"
#out_dir = "D:/2024_04_01_logs/out"
#out_dir = "D:/Otterbein_4_5_24"
out_dir = "D:/Otterbein_04_06_2024/Evening_parsed"
out_dir = "C:/Users/Ruhaan Joshi/Downloads/ewbin"
out_dir = "out"

#dbc_dir = "D:/Downloads/per_dbc.dbc"
dbc_dir = "C:/Users/Ruhaan Joshi/Downloads/per_dbc.dbc"
dbc_dir = "/home/eileen/per/firmware/common/daq/per_dbc.dbc"

le = LogExporter(dbc_dir)

le.parse_files(p, out_dir, fill_empty_vals=True)
