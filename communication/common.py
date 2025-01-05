
import time
from construct import *
from threading import Thread, Event

CAN_EFF_FLAG = 0x80000000
CAN_RTR_FLAG = 0x40000000
CAN_ERR_FLAG = 0x20000000

# DAQ frame encapsulating raw CAN message
DAQFrameStruct = Struct(
    "frame_type" / Hex(Int8ul),
    "tick_ms"    / Hex(Int32ul),
    "msg_id"     / Hex(Int32ul),
    "bus_id"     / Hex(Int8ul),
    "dlc"        / Hex(Int8ul),
    "data"       / Bytes(8),
)
DAQ_FRAME_SIZE = 19
assert(DAQFrameStruct.sizeof() == DAQ_FRAME_SIZE)

# frame type: 8 bit preamble in TCP packet to DAQ
DAQ_FRAME_CAN_RX  = 0  # RX to DAQ over CAN (interrupt), broadcast message
DAQ_FRAME_TCP2CAN = 1  # RX to DAQ over TCP, relay to other nodes on CAN
DAQ_FRAME_TCP2UDS = 2  # RX to DAQ over TCP, process within DAQ (encapsulates CAN msg intended for DAQ)
DAQ_FRAME_TCP_TX  = 3  # TX from DAQ over TCP
DAQ_FRAME_UDP_TX  = 4  # TX from DAQ over UDP

DAQ_FRAME_BUSID_CAN1 = 0
DAQ_FRAME_BUSID_CAN2 = 1

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class DAQAppObject:
    def __init__(self, verbose=False, **kwargs):
        self.verbose = verbose
        self.log_prefix = ""

    def log(self, x, level=0):
        prefix = self.log_prefix + ": " if self.log_prefix else ""
        print(f"LOG: {prefix}{x}")

class StoppableThread(Thread, DAQAppObject):
    def __init__(self, **kwargs):
        super(StoppableThread, self).__init__(**kwargs)
        DAQAppObject.__init__(self, **kwargs)
        self._stop_event = Event()
        self._status_stopped = 0

    def stop(self, timeout=3.0):
        if (self.is_alive()):
            self._stop_event.set()
            start = time.time()
            while (not self._status_stopped) and (time.time() - start < timeout):
                pass
            if (not self._status_stopped):
                self.log("WARN: Failed to wait for thread to stop")
        # Reset
        self._status_stopped = 0
        self._stop_event.clear()

    def stopped(self):
        return self._stop_event.is_set()

    def signal_stopped(self):
        self._status_stopped = 1
