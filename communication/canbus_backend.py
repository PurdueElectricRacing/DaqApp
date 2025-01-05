import atexit
import can
import cantools
import os
import socket
import time
import platform
import usb
import queue
from queue import Queue
from threading import Thread, Event
from construct import *

from .common import *

"""
CANBus API

```
canbus = CANBusUDP()
canbus.connect()
assert(canbus.connected())

canbus.start_thread()
# do stuff here...
msg = canbus.receive_message(timeout=3.0) # rx
canbus.send_message(msg) # tx
canbus.stop_thread()
```

Due to high bus loads each receiver (USB/UDP/TCP) must periodically poll from the hardware (e.g. usb device, udp socket) or else its internal queue will get full and stuck. So each receiver runs a receiver thread (called by start_thread()) in which it pushes the received messages into a python queue. Messages in the queue can be accessed by receive_message().
"""

class CANMessage:
    def __init__(self, raw_msg, dec_msg, dbc_msg):
        self.raw_msg = raw_msg
        self.dec_msg = dec_msg
        self.dbc_msg = dbc_msg
        self.sender = self.dbc_msg.senders[0]

    def __repr__(self):
        t = self.raw_msg.timestamp
        d = "RX" if (self.raw_msg.is_rx) else "TX"
        s = f"  Time: {t:-8.4f} | {d} | ID: 0x{self.raw_msg.arbitration_id:08x} | DL: {self.raw_msg.dlc:1d} | "
        d = ' '.join('{:02x}'.format(x) for x in self.raw_msg.data)
        s += d + "   " * (8 - self.raw_msg.dlc) + " | "
        s += f"{self.dbc_msg.name}"
        p = ' '.join([f"{k}: {v}" for k,v in self.dec_msg.items()])
        s += f"\n   {self.dbc_msg.senders[0]} | {p}"
        s += "\n"
        return s

class CANBusBase(DAQAppObject):
    CANBUS_CONN_USB = 1
    CANBUS_CONN_UDP = 2
    CANBUS_CONN_TCP = 3

    def __init__(self, parent=None, verbose=False):
        super(CANBusBase, self).__init__(verbose)
        self.parent = parent
        self.db = cantools.db.load_file("/home/eileen/per/firmware/common/daq/per_dbc.dbc")
        self.connection_type = 0
        self.rx_buffer = Queue()
        self.listener = StoppableThread(target=self.poll)
        self.msg_count = 0

    def connect(self):
        raise NotImplementedError("Connect")

    def disconnect(self):
        raise NotImplementedError("Connect")

    def connected(self):
        raise NotImplementedError("Connect")

    def receive_message(self):
        raise NotImplementedError("Connect")

    def send_message(self):
        raise NotImplementedError("Connect")

    def send_uds_frame(self):
        raise NotImplementedError("Connect")

    def receive_uds_frame(self):
        raise NotImplementedError("Connect")

    def poll(self):
        raise NotImplementedError("Connect")

    def start_thread(self):
        if (not self.connected()):
            self.log("WARNING: Not connected, cannot start thread")
        else:
            self.listener.start()

    def stop_thread(self):
        self.disconnect()
        atexit.unregister(self.disconnect)

    def receive_message(self, timeout=0.5):
        if (not self.listener.is_alive()):
            #self.log("ERROR: thread not started!")
            return None
        try:
            return self.rx_buffer.get(timeout=timeout)
        except queue.Empty:
            return None

    def receive_decoded_message(self, **kwargs):
        msg = self.receive_message(timeout=1)
        if (msg):
            dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
            dec_msg = dbc_msg.decode(msg.data)
            return CANMessage(raw_msg=msg, dbc_msg=dbc_msg, dec_msg=dec_msg)
        return None

    def _receive_filtered(self, cond, **kwargs):
        while True:
            msg = self.receive_message(**kwargs)
            if (msg) and self.verbose:
                self.log(f" RX: {msg}")
            if (msg) and cond(msg):
                return msg

    def receive_uds_frame(self, node, cmd=0, raw=False, **kwargs):
        rxmsg = self.db.get_message_by_name(f"uds_response_{node.lower()}")
        cond = lambda msg: msg.arbitration_id == rxmsg.frame_id
        if (cmd):
            cond = lambda msg: msg.arbitration_id == rxmsg.frame_id and msg.data[0] & 0xff == cmd
        msg = self._receive_filtered(cond, **kwargs)
        if (raw):
            return msg
        msg = rxmsg.decode(msg.data)
        cmd = msg['payload'] & 0xff
        data = (msg['payload'] >> 8)
        return dotdict({"cmd": cmd, "data": data})

class CANBusUSB(CANBusBase):
    def __init__(self, parent=None, verbose=False):
        super(CANBusUSB, self).__init__(parent, verbose)
        self.connection_type = self.CANBUS_CONN_USB
        self.log_prefix = "USB"
        self.bus = None

    def connect(self, use_gsusb=False):
        # gs_usb is buggy but socketcan only works on windows
        if (platform.system() == "Linux") and (not use_gsusb): # socketcan
            # https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html
            # sudo ip link set can0 up type can bitrate 500000
            bus = can.ThreadSafeBus(bustype='socketcan', channel='can0', bitrate=500000, receive_own_messages=True)
            self.bus = bus
            self.log("Connected via canable socketcan")
            atexit.register(self.disconnect)
            return True
        else: # gs_usb
            dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F) # canable ID
            if (dev == None):
                self.log("Failed to find canable USB device")
                return False
            else:
                channel = dev.product
                bus_num = dev.bus
                addr = dev.address
                del(dev)
                bus = can.ThreadSafeBus(bustype="gs_usb", channel=channel, bus=bus_num, address=addr, bitrate=500000, receive_own_messages=True)
                while (bus.recv(0)): pass
                self.bus = bus
                self.log("Connected via canable gs_usb")
                atexit.register(self.disconnect)
                return True

    def disconnect(self):
        self.listener.stop()
        self.bus.shutdown()
        if (platform.system() != "Linux"):
            usb.util.dispose_resources(self.bus.gs_usb.gs_usb)
        del(self.bus)
        self.bus = None
        self.log("Disconnected from canable usb")
        atexit.unregister(self.disconnect)

    def connected(self):
        return not not self.bus

    def send_message(self, msg: can.Message, **kwargs):
        x = self.bus.send(msg)
        while True:
            ack = self.receive_message(timeout=1)
            if ack and self.verbose:
                self.log(f"ACK: {ack}")
            if (ack) and (msg.arbitration_id == ack.arbitration_id):
                break
        return

    def send_uds_frame(self, node, cmd, data, **kwargs):
        txmsg = self.db.get_message_by_name(f"uds_command_{node.lower()}")
        if (isinstance(data, int)):
            data = txmsg.encode({"payload": (cmd & 0xff) | (data << 8)})
        return self.send_message(can.Message(arbitration_id=txmsg.frame_id, data=data), **kwargs)

    def poll(self):
        while not self.listener.stopped():
            # try to get a message
            msg, already_filtered = self.bus._recv_internal(timeout=1)
            if msg:
                self.rx_buffer.put(msg)
                self.msg_count += 1
        self.listener.signal_stopped()

class CANBusUDPTCP(CANBusBase):
    def __init__(self, parent=None, verbose=False):
        super(CANBusUDPTCP, self).__init__(parent, verbose)
        self.sock = None

    def connected(self):
        return not not self.sock

    def _bytes_to_message(self, b):
        frame = DAQFrameStruct.parse(b)
        # TODO check DAQ frame frame_type based on UDP/TCP + classify
        # TODO: sanity check on these values in case of corrupted messages.
        ts = frame.tick_ms / 1000.0
        can_id = frame.msg_id

        # decompose ID
        is_extended = bool(can_id & CAN_EFF_FLAG)
        if is_extended:
            arb_id = can_id & 0x1FFFFFFF
        else:
            arb_id = can_id & 0x000007FF

        return can.Message(
            timestamp = ts,
            arbitration_id = arb_id,
            is_extended_id = is_extended,
            is_error_frame = bool(can_id & CAN_ERR_FLAG),
            is_remote_frame = bool(can_id & CAN_RTR_FLAG),
            dlc=frame.dlc,
            channel=frame.bus_id,
            data=frame.data,
        )

    def _receive_message_internal(self, count=1, buffer_count=32, timeout=1.0, **kwargs): # TODO timeout UDP
        part = b''
        msgs = []
        start = time.time()
        while (len(msgs) < count) and (time.time() - start < timeout):
            try:
                data = self.sock.recv(DAQ_FRAME_SIZE * buffer_count)
            except socket.timeout:
                if (time.time() - start >= timeout):
                    break
                # no data, just try again
                continue
            except OSError as e:
                if (time.time() - start >= timeout):
                    break
                # socket's been closed
                self.log(f"ERROR: connection closed (1): {e}")
                break # lol
            if (len(data)):
                # process the 1 or more messages we just received
                if (len(part)):
                    data = part + data # add on the previous remainder
                # check how many whole and incomplete messages we got through.
                num_incomplete_bytes = len(data) % DAQ_FRAME_SIZE
                num_frames = len(data) // DAQ_FRAME_SIZE
                # to pre-pend next time:
                if num_incomplete_bytes:
                    part = data[-num_incomplete_bytes:]
                else:
                    part = b''

                for n in range(num_frames):
                    msg_buf = data[n*DAQ_FRAME_SIZE:(n+1)*DAQ_FRAME_SIZE]
                    msg = self._bytes_to_message(msg_buf) # skip 8 bit cmd
                    msgs.append(msg)
        return msgs

class CANBusUDP(CANBusUDPTCP):
    def __init__(self, parent=None, verbose=False):
        super(CANBusUDP, self).__init__(parent, verbose)
        self.connection_type = self.CANBUS_CONN_UDP
        self.log_prefix = "UDP"

    def connect(self, port=5005):
        # open socket and wait for connection to establish.
        socket.setdefaulttimeout(3) # seconds
        # ip addr add 192.168.10.1/24 dev eth0
        # sudo ifconfig eth0 192.168.10.255 netmask 255.255.255.0
        self.log("Attempting to connect to UDP")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.bind(("", port)) # any addr
        sock.settimeout(0.5) # blocking makes exiting an infinite loop hard
        self.sock = sock
        self.log(f"Tuned in to DAQ UDP broadcast: {self.sock}")
        self.log("Warning: UDP does not guarantee a connection")
        atexit.register(self.disconnect)

    def disconnect(self):
        self.listener.stop()
        self.sock.close()
        self.sock = None
        self.log("Disconnected from DAQ UDP broadcast")
        atexit.unregister(self.disconnect)

    def send_message(self, msg: can.Message):
        raise RuntimeError("No UDP send!")

    def send_uds_frame(self, msg: can.Message):
        raise RuntimeError("No UDP send!")

    def poll(self):
        while not self.listener.stopped():
            # try to get a message
            msgs = self._receive_message_internal(count=1, buffer_count=20)
            for msg in msgs:
                self.rx_buffer.put(msg)
                self.msg_count += 1
        self.listener.signal_stopped()

class CANBusTCP(CANBusUDPTCP):
    def __init__(self, parent=None, verbose=False):
        super(CANBusTCP, self).__init__(parent, verbose)
        self.connection_type = self.CANBUS_CONN_TCP
        self.log_prefix = "TCP"
        #self.tx_buffer = Queue()

    def connect(self, ip="192.168.10.41", port=5005):
        # open socket and wait for connection to establish.
        socket.setdefaulttimeout(3) # seconds
        # ip addr add 192.168.10.1/24 dev eth0
        # sudo ifconfig eth0 192.168.10.255 netmask 255.255.255.0
        self.log("Attempting to connect to TCP")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        try:
            sock.connect((ip, port))
        except OSError:
            self.log("Failed to establish TCP connection")
            return False
        sock.settimeout(1) # blocking makes exiting an infinite loop hard
        self.sock = sock
        self.log("Established DAQ TCP: ")
        self.log(self.sock)
        atexit.register(self.disconnect)
        return True

    def disconnect(self):
        self.listener.stop()
        self.sock.close()
        self.sock = None
        self.log("Disconnected from DAQ TCP")
        atexit.unregister(self.disconnect)

    # TCP message (to DAQ) encapsulates a raw CAN message with a 8-bit starting identifier
    # specifying whether it's for DAQ or the other nodes
    def send_message(self, msg: can.Message, frame_type=1, bus_id=0):
        if msg.is_extended_id:
            msg.arbitration_id |= CAN_EFF_FLAG
        if msg.is_remote_frame:
            msg.arbitration_id |= CAN_RTR_FLAG
        if msg.is_error_frame:
            msg.arbitration_id |= CAN_ERR_FLAG

        frame_buf = DAQFrameStruct.build(dict(
            frame_type=frame_type,
            tick_ms=0, #// int(round(time.time() * 1000)) & 0xffffffff
            msg_id=msg.arbitration_id,
            bus_id=bus_id,
            dlc=msg.dlc,
            data=msg.data,
        ))
        #self.tx_buffer.put(frame_buf)
        self.sock.sendall(frame_buf)
        return True

    def send_uds_frame(self, node, cmd, data):
        txmsg = self.db.get_message_by_name(f"uds_command_{node.lower()}")
        if (isinstance(data, int)):
            data = txmsg.encode({"payload": (cmd & 0xff) | (data << 8)})
        frame_type = DAQ_FRAME_TCP2UDS if node.lower() == "daq" else DAQ_FRAME_TCP2CAN
        return self.send_message(can.Message(arbitration_id=txmsg.frame_id, data=data), frame_type=frame_type)

    def poll(self):
        while not self.listener.stopped():
            #tx_data = b''
            #while not self.tx_buffer.empty(): #we know there's one message, might be more.
            #    tx_data += self.tx_buffer.get()
            #if (len(tx_data)):
            #    self.sock.sendall(tx_data)
            # try to get a message
            msgs = self._receive_message_internal(count=1, buffer_count=1)
            for msg in msgs:
                #self.log(f"TCP RX: {msg}")
                self.rx_buffer.put(msg)
                self.msg_count += 1
        self.listener.signal_stopped()
