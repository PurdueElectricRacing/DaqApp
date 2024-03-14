from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import can
import can.interfaces.gs_usb
import gs_usb
import socket
import usb
import cantools
from communication.client import TCPBus, UDPBus
from communication.connection_error_dialog import ConnectionErrorDialog
from communication.bind_error import BindError
from communication.password_dialog import PasswordDialog
import utils
import time
import threading
import numpy as np
import math


class CanBus(QtCore.QThread):
    """
    Handles sending and receiving can bus messages,
    tracks all degined signals (BusSignal)
    """

    connect_sig = QtCore.pyqtSignal(bool)
    write_sig = QtCore.pyqtSignal(int)
    bus_load_sig = QtCore.pyqtSignal(float)
    new_msg_sig = QtCore.pyqtSignal(can.Message)
    daq_msg_sig = QtCore.pyqtSignal(can.Message)
    flt_msg_sig = QtCore.pyqtSignal(can.Message)
    bl_msg_sig = QtCore.pyqtSignal(can.Message)

    def __init__(self, dbc_path, default_ip, can_config: dict):
        super(CanBus, self).__init__()
        self.db = cantools.db.load_file(dbc_path)

        utils.log(f"CAN version: {can.__version__}")
        utils.log(f"gs_usb version: {gs_usb.__version__}")

        self.connected = False
        self.bus = None
        self.start_time_bus = -1
        self.start_date_time_str = ""
        self.tcp = False
        self.tcpbus = None

        # Bus Load Estimation
        self.total_bits = 0
        self.last_estimate_time = 0

        # Load Bus Signals
        self.can_config = can_config
        self.updateSignals(self.can_config)

        self.is_importing = False

        #self.port = 8080
        self.port = 5005
        self.ip = default_ip
        #self.ip = "10.42.0.1"
        self.password = None
        self.is_wireless = False


    def connect(self):
        """ Connects to the bus """
        utils.log("Trying usb")
        # Attempt usb connection first
        dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
        if dev:
            channel = dev.product
            bus_num = dev.bus
            addr = dev.address
            del(dev)
            self.bus = can.ThreadSafeBus(bustype="gs_usb", channel=channel, bus=bus_num, address=addr, bitrate=500000)
            # Empty buffer of old messages
            while(self.bus.recv(0)): pass
            self.connected = True
            self.is_wireless = False
            self.connect_sig.emit(self.connected)
            utils.log("Usb successful")
            return

        #USB Failed, trying UDP
        utils.log("Trying UDP")
        try:
            self.bus = UDPBus(self.ip, self.port)
            self.connected = True
            self.is_wireless = True
            # Empty buffer of old messages
            time.sleep(3)
            i=0
            while(self.bus.recv(0)):
                i+=1
            utils.log(f"cleared {i} from buffer")
            utils.log_warning("This does not gurantee a connection. Please make sure Raspberry Pi is broadcasting.")
            self.connect_sig.emit(self.connected)
            return
        except OSError as e:
            utils.log(f"UDP connect error {e}")

        # Usb failed, trying tcp
        # utils.log("Trying tcp")
        # try:
        #     self.bus = TCPBus(self.ip, self.port)
        #     self.connected = True
        #     self.is_wireless = True
        #     # Empty buffer of old messages
        #     time.sleep(3)
        #     i=0
        #     while(self.bus.recv(0)):
        #         i+=1
        #     utils.log(f"cleared {i} from buffer")
        #     utils.log("Tcp successful")
        #     self.connect_sig.emit(self.connected)
        #     return
        # except OSError as e:
        #     utils.log(f"tcp connect error {e}")

        #Both Connections Failed
        self.connected = False
        utils.log_error("Failed to connect to a bus")
        self.connect_sig.emit(self.connected)
        self.connectError()

    def connect_tcp(self):
        # Usb failed, trying tcp
        utils.log("Trying tcp")
        self.connected_disp = 1
        self.write_sig.emit(self.connected_disp)
        try:
            self.tcpbus = TCPBus(self.ip, self.port)
            self.connected_tcp = True
            # Empty buffer of old messages
            # time.sleep(3)
            i=0
            while(self.tcpbus.recv(0)):
                i+=1
            utils.log(f"cleared {i} from buffer")
            utils.log("Tcp successful")
            # self.password = PasswordDialog.promptPassword(self.password)
            # print(self.password)
            # result = True
            # if self.password == "":
            #     result = False
            # elif self.password == None:
            #     self.tcpbus.shutdown(0)
            #     result = True
            # else:
            #     result = self.tcpbus.handshake(self.password)
            # while not result:
            #     self.password = None
            #     self.password = PasswordDialog.setText(self.password)
            #     if self.password == "":
            #         result = False
            #     elif self.password == None:
            #         self.tcpbus.shutdown(0)
            #         result = True
            #     else:
            #         result = self.tcpbus.handshake(self.password)
            # # self.connect_sig.emit(self.connected)
            self.connected_disp = 2
            self.write_sig.emit(self.connected_disp)
            self.tcp = True
            return
        except socket.timeout as e:
            self.connected_disp = 0
            self.write_sig.emit(self.connected_disp)
            utils.log_error(e)
            BindError.bindError()
            self.tcpbus.close()
            return
        except Exception as e:
            utils.log(f"Unknown Error: {e}")
        # except OSError as e:
        #     utils.log(f"tcp connect error {e}")

        #TCP Connection is in Bind State
        # self.connected_disp = False
        utils.log_error("Failed to connect to the TCP")
        # self.connect_sig.emit(self.connected_disp)
        # BindError.bindError()
        self.connectError()
        self.connected_disp = 0
        self.write_sig.emit(self.connected_disp)



    def disconnect_bus(self):
        self.connected = False
        self.connect_sig.emit(self.connected)
        if self.tcpbus:
            self.disconnect_tcp()
        if self.bus:
            self.bus.shutdown()
            if not self.is_wireless: usb.util.dispose_resources(self.bus.gs_usb.gs_usb)
            del(self.bus)
            self.bus = None

    def disconnect_tcp(self):
        self.connected_disp = 0
        self.write_sig.emit(self.connected_disp)
        if self.tcpbus:
            self.tcpbus.shutdown(1)
            del(self.tcpbus)
            self.tcpbus = None


    def reconnect(self):
        """ destroy usb connection, attempt to reconnect """
        self.connected = False
        while(not self.isFinished()):
            # wait for bus receive to finish
            pass
        self.disconnect_bus()
        time.sleep(1.5)
        self.connect()
        utils.clearDictItems(utils.signals)
        self.start_time_bus = -1
        self.start_time_cmp = 0
        self.start_date_time_str = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        self.start()

    def sendLogCmd(self, option : bool):
        """Send the start logging function"""
        if self.tcp and self.tcpbus:
            if option == True:
                self.tcpbus.start_logging()
            else:
                self.tcpbus.stop_logging()
        else:
            utils.log_warning('Must connect to TCP bus to control logging, please click write to car')

    def sendFormatMsg(self, msg_name, msg_data: dict):
        """ Sends a message using a dictionary of its data """
        dbc_msg = self.db.get_message_by_name(msg_name)
        data = dbc_msg.encode(msg_data)
        msg = can.Message(arbitration_id=dbc_msg.frame_id, data=data, is_extended_id=True)
        if self.tcp:
            self.tcpbus.send(msg)
        else:
            self.bus.send(msg)

    def sendMsg(self, msg: can.Message):
        """ Sends a can message over the bus """
        if self.connected:
            if self.is_wireless:
                if self.tcpbus:
                    self.tcpbus.send(msg)
                else:
                    utils.log_warning('Unable to send message, please click write to car')
            else:
                self.bus.send(msg)
        else:
            utils.log_error("Tried to send msg without connection")
        
    def updateStartTime(self, new_time):
        self.start_time_bus = new_time
        self.start_time_cmp = time.time()
        self.start_date_time_str = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        utils.log_warning(f"Start time changed: {new_time}")
        self.out_of_order_cnt = 0

    def onMessageReceived(self, msg: can.Message):
        """ Emits new message signal and updates the corresponding signals """
        if self.start_time_bus == -1:
            self.updateStartTime(msg.timestamp)
        if msg.timestamp - self.start_time_bus < 0:
            utils.log_warning("Out of order")
            self.out_of_order_cnt = self.out_of_order_cnt + 1
            if (self.out_of_order_cnt > 50): self.updateStartTime(msg.timestamp)
                
        msg.timestamp -= self.start_time_bus
        self.new_msg_sig.emit(msg) 
        if (msg.arbitration_id >> 6) & 0xFFFFF == 0xFFFFF: self.daq_msg_sig.emit(msg) # Check if it could be daq
        if (msg.arbitration_id & (0x1C000000) != 0): self.flt_msg_sig.emit(msg) # Check for HLP = 0
        if (msg.arbitration_id & 0x3F == 60): self.bl_msg_sig.emit(msg) # emit for bootloader
        if not msg.is_error_frame:
            dbc_msg = None
            try:
                dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                decode = dbc_msg.decode(msg.data)
                for sig in decode.keys():
                    sig_val = decode[sig]
                    if (type(sig_val) != str):
                        utils.signals[utils.b_str][dbc_msg.senders[0]][dbc_msg.name][sig].update(sig_val, msg.timestamp, not utils.logging_paused or self.is_importing)
            except KeyError:
                if dbc_msg and "daq" not in dbc_msg.name and "fault" not in dbc_msg.name:
                    if utils.debug_mode: utils.log_warning(f"Unrecognized signal key for {msg}")
                # elif "fault" not in dbc_msg.name:
                #     if utils.debug_mode: utils.log_warning(f"unrecognized: {msg.arbitration_id}")
            except ValueError as e:
                if "daq" not in dbc_msg.name:
                    if utils.debug_mode: utils.log_warning(f"Failed to convert msg: {msg}")
                    print(e)
        # if (msg.is_error_frame):
        #     utils.log(msg)

        # bus load estimation
        msg_bit_length_max = 64 + msg.dlc * 8 + 18
        self.total_bits += msg_bit_length_max

    def pause(self, pause: bool):
        """ pauses the recording of signal values, passes through read requests """
        utils.logging_paused = pause

    def connectError(self):
        """ Creates message box prompting to try to reconnect """
        self.ip = ConnectionErrorDialog.connectionError(self.ip)
        if self.ip:
            self.connect_tcp()


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
                                    = BusSignal.fromCANMsg(signal, msg, node, bus)

    def run(self):
        """ Thread loop to receive can messages """
        self.last_estimate_time = time.time()
        loop_count = 0
        skips = 0
        avg_process_time = 0

        #while self.connected:
        while (not self.is_wireless or self.bus and self.bus._is_connected) and self.connected:
            # TODO: detect when not connected (add with catching send error)
            #       would the connected variable need to be locked?
            msg = self.bus.recv(0.25)
            if msg:
                delta = time.perf_counter()
                if not self.is_importing:
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
                # if loop_count != 0 and loop_count-skips != 0 and utils.debug_mode: print(f"rx period (ms): {1/loop_count*1000}, skipped: {skips}, process time (ms): {avg_process_time / (loop_count-skips)*1000}")
                loop_count = 0
                avg_process_time = 0
                skips = 0
        #self.connect_sig.emit(self.connected and self.bus.is_connected)
        if (self.connected and self.is_wireless): self.connect_sig.emit(self.bus and self.bus.is_connected)


class BusSignal(QtCore.QObject):
    """ Signal that can be subscribed (connected) to for updates """

    update_sig = QtCore.pyqtSignal()
    history = 500000#240000 # for 0.015s update period 1 hour of data
    data_lock = threading.Lock()

    def __init__(self, bus_name, node_name, msg_name, sig_name, dtype, store_dtype=None, unit="", msg_desc="", sig_desc="", msg_period=0):
        super(BusSignal, self).__init__()
        self.bus_name = bus_name
        self.node_name = node_name
        self.message_name = msg_name
        self.signal_name = sig_name

        self.unit = unit
        self.msg_desc = msg_desc
        self.sig_desc = sig_desc
        self.msg_period = msg_period
        self.send_dtype = dtype
        if not store_dtype: self.store_dtype = self.send_dtype
        else: self.store_dtype = store_dtype
        self.curr_idx = 0
        self.data  = np.zeros(self.history, dtype=self.store_dtype)
        self.times = np.zeros(self.history, dtype=np.float32)
        self.color = QtGui.QColor(255, 255, 255)
        self.stale_timestamp = time.time()
        if not utils.dark_mode:
            self.color = QtGui.QColor(0,0,0)

    def fromCANMsg(sig, msg, node, bus):
        send_dtype = utils.data_types[sig['type']]
        # If there is scaling going on, don't store as an integer on accident
        if ('scale' in sig and sig['scale'] != 1) or ('offset' in sig and sig['offset'] != 0):
            parse_dtype = utils.data_types['float']
        else:
            parse_dtype = send_dtype
        return BusSignal(bus['bus_name'], node['node_name'], msg['msg_name'], sig['sig_name'],
                         send_dtype, store_dtype=parse_dtype,
                         unit=(sig['unit'] if 'unit' in sig else ""),
                         msg_desc=(msg['msg_desc'] if 'msg_desc' in msg else ""),
                         sig_desc=(sig['sig_desc'] if 'sig_desc' in sig else ""),
                         msg_period=msg['msg_period'])

    def connect(self, func: 'function'):
        """ call func each time signal updated """
        self.update_sig.connect(func)

    def disconnect(self, func: 'function'):
        """ stop calling func on signal update """
        self.update_sig.disconnect(func)

    def update(self, val, timestamp, record):
        """ update the value of the signal """
        if record: self.curr_idx += 1
        if self.curr_idx >= self.history:
            utils.log_warning(f"{self.signal_name} out of space, resetting!")
            self.clear()
        with self.data_lock:
            self.data[self.curr_idx] = val
            self.times[self.curr_idx] = timestamp
            self.stale_timestamp = time.time()
        self.update_sig.emit()

    def clear(self):
        """ clears stored signal values """
        with self.data_lock:
            self.curr_idx = 0
            self.data.fill(0)
            self.times.fill(0)

    @property
    def curr_val(self):
        """ last value recorded """
        with self.data_lock:
            return self.data[self.curr_idx]

    @property
    def last_update_time(self):
        """ timestamp of last value recorded """
        with self.data_lock:
            return self.times[self.curr_idx]

    @property
    def length(self):
        """ number of recorded values """
        return self.curr_idx

    @property
    def is_stale(self):
        """ based on last receive time """
        if self.msg_period == 0: return False
        else:
            return ((time.time() - self.stale_timestamp) * 1000) > self.msg_period * 1.5
