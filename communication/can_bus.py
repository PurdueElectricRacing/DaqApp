from PyQt5 import QtWidgets, QtCore
import can
import usb
import cantools
import utils
import time

# TODO: requirements file for python libs
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
        # TODO: implement bus selection
        #self.bus_name = "Main"

        # Bus Load Estimation
        self.total_bits = 0
        self.last_estimate_time = 0

        # Load Bus Signals
        self.can_config = can_config
        self.signals = {}
        self.updateSignals(self.can_config)

    def connect(self):
        """ Connects to the USB cannable """
        dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
        if dev:
            channel = dev.product
            bus_num = dev.bus
            addr = dev.address
            del(dev)
            self.bus = can.Bus(bustype="gs_usb", channel=channel, bus=bus_num, address=addr, bitrate=500000)
            self.connected = True
        else:
            self.connected = False
            utils.log_error("Failed to connect to USB Cannable")
            self.connectError()
        self.connect_sig.emit(self.connected)
    
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
        self.new_msg_sig.emit(msg)
        try:
            dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
            decode = dbc_msg.decode(msg.data)
            for sig in decode.keys():
                self.signals['Main'][dbc_msg.senders[0]][dbc_msg.name][sig].update(decode[sig])
        except KeyError:
            utils.log_warning(f"Unrecognized signal key for {msg}")
        except ValueError:
            #utils.log_warning(f"Failed to convert msg: {msg}")
            pass

        # bus load estimation
        msg_bit_length_max = 64 + msg.dlc * 8 + 18 
        self.total_bits += msg_bit_length_max

    def connectError(self):
        """ Creates message box prompting to try to reconnect """
        msgBox = QtWidgets.QMessageBox(self.parent())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText("Failed to connect to USB Cannable")
        msgBox.setWindowTitle("Connection Error")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Cancel)
        msgBox.buttons()[0].clicked.connect(self.connect)
        msgBox.buttons()[1].clicked.connect(quit)
        msgBox.exec_()

    def updateSignals(self, can_config: dict):
        """ Creates dictionary of BusSignals of all signals in can_config """
        self.signals.clear()
        for bus in can_config['busses']:
            self.signals[bus['bus_name']] = {}
            for node in bus['nodes']:
                self.signals[bus['bus_name']][node['node_name']] = {}
                for msg in node['tx']:
                    self.signals[bus['bus_name']][node['node_name']][msg['msg_name']] = {}
                    for signal in msg['signals']:
                        self.signals[bus['bus_name']][node['node_name']] \
                                    [msg['msg_name']][signal['sig_name']]\
                                    = BusSignal(bus['bus_name'], node['node_name'],
                                                msg['msg_name'], signal['sig_name'])

    def run(self):
        """ Thread loop to receive can messages """
        self.last_estimate_time = time.time()

        while self.connected:
            # TODO: detect when not connected (add with catching send error)
            #       would the connected variable need to be locked?
            msg = self.bus.recv(0.25)
            if msg:
                self.onMessageReceived(msg)
            
            # Bus load estimation
            if (time.time() - self.last_estimate_time) > 1:
                self.last_estimate_time = time.time()
                bus_load = self.total_bits / 500000.0 * 100
                self.total_bits = 0
                self.bus_load_sig.emit(bus_load)


class BusSignal(QtCore.QObject):
    """ Signal that can be subscribed (connected) to for updates """

    update_sig = QtCore.pyqtSignal()

    def __init__(self, bus_name, node_name, message_name, signal_name):
        super(BusSignal, self).__init__()
        self.bus_name = bus_name
        self.node_name = node_name
        self.message_name = message_name
        self.signal_name = signal_name
        self.curr_val = 0
        self.last_update_time = 0

    def connect(self, func: 'function'):
        self.update_sig.connect(func)

    def disconnect(self):
        # TODO: don't disconnect all, only the one that wants to
        self.update_sig.disconnect()

    def update(self, val):
        self.curr_val = val
        self.last_update_time = time.time()
        self.update_sig.emit()