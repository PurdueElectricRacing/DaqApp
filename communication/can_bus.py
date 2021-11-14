from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import can
import usb
import cantools
from communication.client import TCPBus
from communication.connection_error_dialog import ConnectionErrorDialog
import utils
import time
import threading
import numpy as np
import math

# TODO: selection for bustype: gs_usb or socket
class CanBus(QtCore.QThread):
    """
    Handles sending and receiving can bus messages, 
    tracks all degined signals (BusSignal)
    """

    connect_sig = QtCore.pyqtSignal(bool)
    bus_load_sig = QtCore.pyqtSignal(float)
    new_msg_sig = QtCore.pyqtSignal(can.Message)

    def __init__(self, dbc_path, can_config: dict):
        super(CanBus, self).__init__()
        self.db = cantools.db.load_file(dbc_path)

        self.connected = False
        self.start_time = -1
        self.start_date_time_str = ""
        # TODO: implement bus selection
        #self.bus_name = "Main"

        # Bus Load Estimation
        self.total_bits = 0
        self.last_estimate_time = 0

        # Load Bus Signals
        self.can_config = can_config
        self.updateSignals(self.can_config)

        self.is_paused = True

        self.port = 8080
        self.ip = '169.254.48.90'
        self.is_wireless = False

    
    def connect(self):
        """ Connects to the bus """
        # Attempt usb connection first
        dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
        if dev:
            channel = dev.product
            bus_num = dev.bus
            addr = dev.address
            del(dev)
            self.bus = can.Bus(bustype="gs_usb", channel=channel, bus=bus_num, address=addr, bitrate=500000)
            # Empty buffer of old messages
            while(self.bus.recv(0)): pass
            self.connected = True
            self.is_wireless = False
            self.connect_sig.emit(self.connected)
            return

        # Usb failed, trying tcp
        try:
            self.bus = TCPBus(self.ip, self.port)
            self.connected = True
            self.is_wireless = True
            self.connect_sig.emit(self.connected)
            return
        except OSError:
            pass # failed to connect

        self.connected = False
        utils.log_error("Failed to connect to a bus")
        self.connect_sig.emit(self.connected)
        self.connectError()

    def reconnect(self):
        """ destroy usb connection, attempt to reconnect """
        self.connected = False
        while(not self.isFinished()):
            # wait for bus receive to finish
            pass
        self.bus.shutdown()
        if not self.is_wireless: usb.util.dispose_resources(self.bus.gs_usb.gs_usb)
        del(self.bus)
        self.connect()
        self.start()
        utils.clearDictItems(utils.signals)
        self.start_time = -1
        self.start_date_time_str = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    
    def sendFormatMsg(self, msg_name, msg_data: dict):
        """ Sends a message using a dictionary of its data """
        dbc_msg = self.db.get_message_by_name(msg_name)
        data = dbc_msg.encode(msg_data)
        msg = can.Message(arbitration_id=dbc_msg.frame_id, data=data, is_extended_id=True)
        self.bus.send(msg)
    
    def sendMsg(self, msg: can.Message):
        """ Sends a can message over the bus """
        if self.connected:
            self.bus.send(msg)
        else:
            utils.log_error("Tried to send msg without connection")
    
    def onMessageReceived(self, msg: can.Message):
        """ Emits new message signal and updates the corresponding signals """
        if self.start_time == -1: 
            self.start_time = msg.timestamp
            self.start_date_time_str = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        msg.timestamp -= self.start_time
        self.new_msg_sig.emit(msg) # TODO: only emit signal if DAQ msg for daq_protocol, currently receives all msgs (low priority performance improvement)
        if not self.is_paused:
            try:
                dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                decode = dbc_msg.decode(msg.data)
                for sig in decode.keys():
                    utils.signals['Main'][dbc_msg.senders[0]][dbc_msg.name][sig].update(decode[sig], msg.timestamp)
            except KeyError:
                utils.log_warning(f"Unrecognized signal key for {msg}")
            except ValueError:
                #utils.log_warning(f"Failed to convert msg: {msg}")
                pass

        # bus load estimation
        msg_bit_length_max = 64 + msg.dlc * 8 + 18 
        self.total_bits += msg_bit_length_max

    def pause(self, pause: bool):
        """ pauses the recording of signal values, passes through read requests """
        self.is_paused = pause

    def connectError(self):
        """ Creates message box prompting to try to reconnect """
        self.ip = ConnectionErrorDialog.connectionError(self.ip)
        self.connect()


    def updateSignals(self, can_config: dict):
        """ Creates dictionary of BusSignals of all signals in can_config """
        utils.signals.clear()
        for bus in can_config['busses']:
            utils.signals[bus['bus_name']] = {}
            for node in bus['nodes']:
                utils.signals[bus['bus_name']][node['node_name']] = {}
                for msg in node['tx']:
                    utils.signals[bus['bus_name']][node['node_name']][msg['msg_name']] = {}
                    for signal in msg['signals']:
                        utils.signals[bus['bus_name']][node['node_name']] \
                                    [msg['msg_name']][signal['sig_name']]\
                                    = BusSignal(bus['bus_name'], node['node_name'],
                                                msg['msg_name'], signal['sig_name'], np.dtype('<u'+str(math.ceil(signal['length']/8))))

    def run(self):
        """ Thread loop to receive can messages """
        self.last_estimate_time = time.time()
        loop_count = 0
        skips =0
        avg_process_time = 0

        while self.connected:
            # TODO: detect when not connected (add with catching send error)
            #       would the connected variable need to be locked?
            msg = self.bus.recv(0.25)
            if msg:
                delta = time.perf_counter()
                self.onMessageReceived(msg)
                avg_process_time += time.perf_counter() - delta
            else:
                skips += 1

            loop_count += 1
            # Bus load estimation
            if (time.time() - self.last_estimate_time) > 1:
                self.last_estimate_time = time.time()
                bus_load = self.total_bits / 500000.0 * 100
                self.total_bits = 0
                self.bus_load_sig.emit(bus_load)

                if loop_count != 0 and loop_count-skips != 0: print(f"rx period (ms): {1/loop_count*1000}, skipped: {skips}, process time (ms): {avg_process_time / (loop_count-skips)*1000}")
                loop_count = 0
                avg_process_time = 0
                skips = 0
        self.bus.shutdown()


class BusSignal(QtCore.QObject):
    """ Signal that can be subscribed (connected) to for updates """

    update_sig = QtCore.pyqtSignal()
    history = 240000 # for 0.015s update period 1 hour of data
    data_lock = threading.Lock()

    def __init__(self, bus_name, node_name, message_name, signal_name, d_type):
        super(BusSignal, self).__init__()
        self.bus_name = bus_name
        self.node_name = node_name
        self.message_name = message_name
        self.signal_name = signal_name
        self.next_idx = 0
        self.data  = np.zeros(self.history, dtype=d_type)
        self.times = np.zeros(self.history, dtype=np.float)
        self.color = QtGui.QColor(255, 255, 255)

    def connect(self, func: 'function'):
        """ call func each time signal updated """
        self.update_sig.connect(func)

    def disconnect(self, func: 'function'):
        """ stop calling func on signal update """
        self.update_sig.disconnect(func)

    def update(self, val, timestamp):
        """ update the value of the signal """
        with self.data_lock:
            if self.next_idx >= self.history:
                utils.log_warning(f"{self.signal_name} out of space, resetting!")
                self.clear()
            self.data[self.next_idx] = val
            self.times[self.next_idx] = timestamp
            self.next_idx += 1
        self.update_sig.emit()

    def clear(self):
        """ clears stored signal values """
        with self.data_lock:
            self.next_idx = 0
            self.data.fill(0)
            self.times.fill(0)

    @property
    def curr_val(self):
        """ last value recorded """
        with self.data_lock:
            return self.data[self.next_idx - 1]

    @property
    def last_update_time(self):
        """ timestamp of last value recorded """
        with self.data_lock:
            return self.times[self.next_idx - 1]
    
    @property
    def length(self):
        """ number of recorded values """
        return self.next_idx