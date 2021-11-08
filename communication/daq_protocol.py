from communication.can_bus import BusSignal, CanBus
from PyQt5 import QtCore
import utils
import can
import math
import numpy as np

DAQ_CMD_LENGTH    = 3
DAQ_CMD_MASK      = 0b111
DAQ_CMD_READ      = 0
DAQ_CMD_WRITE     = 1
DAQ_CMD_LOAD      = 2
DAQ_CMD_SAVE      = 3
DAQ_CMD_PUB_START = 4
DAQ_CMD_PUB_STOP  = 5

DAQ_RPLY_READ        = 0
DAQ_RPLY_SAVE        = 1
DAQ_RPLY_READ_ERROR  = 2
DAQ_RPLY_WRITE_ERROR = 3
DAQ_RPLY_SAVE_ERROR  = 4
DAQ_RPLY_LOAD_ERROR  = 5
DAQ_RPLY_PUB         = 6

DAQ_ID_LENGTH = 5
DAQ_ID_MASK   = 0b11111


class DAQVariable(BusSignal):
    """ DAQ variable that can be subscribed (connected) to for receiving updates"""

    def __init__(self, bus_name, node_name, message_name, signal_name, daq_id, read_only, 
                 bit_length, eeprom_enabled):
        super(DAQVariable, self).__init__(bus_name, node_name, 
                                          message_name, signal_name, np.dtype('<u'+str(math.ceil(bit_length/8))))
        self.id = daq_id
        self.read_only = read_only
        self.bit_length = bit_length
        self.eeprom_enabled = eeprom_enabled
        self.pub_period_ms = 0

class DaqProtocol(QtCore.QObject):
    """ Implements CAN daq protocol for modifying and live tracking of variables """

    save_in_progress_sig = QtCore.pyqtSignal(bool)

    def __init__(self, bus: CanBus, daq_config: dict):
        super(DaqProtocol, self).__init__()
        self.can_bus = bus
        self.can_bus.new_msg_sig.connect(self.handleDaqMsg)

        self.updateVarDict(daq_config)

        # eeprom saving (prevent a load while save taking place)
        self.last_save_request_id = 0
        self.save_in_progress = False

    def readVar(self, var: DAQVariable):
        """ Requests to read a variable, expects a reply """
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_READ]
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))

    def writeVar(self, var: DAQVariable, new_val):
        """ Writes to a variable """
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_WRITE]
        # LSB, add variable data to byte array
        for i in range(math.ceil(var.bit_length / 8)):
            data.append((new_val >> i * 8) & 0xFF)
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))
        
    def saveVar(self, var: DAQVariable):
        """ Saves variable state in eeprom, expects save complete reply """
        if not var.eeprom_enabled:
            utils.log_error(f"Invalid save var operation for {var.signal_name}")
            return
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_SAVE]
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                        is_extended_id=True,
                                        data=data))
        self.save_in_progress = True
        self.last_save_request_id = var.id
        self.save_in_progress_sig.emit(True)
    
    def loadVar(self, var: DAQVariable):
        """ Loads a variable from eeprom, cannot be performed during save operation """
        if not var.eeprom_enabled or var.read_only:
            utils.log_error(f"Invalid load var operation for {var.signal_name}")
            return
        if self.save_in_progress:
            utils.log_error(f"Cannot load var during save operation ")
            return
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_LOAD]
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))

    def pubVar(self, var: DAQVariable, period_ms):
        """ Requests to start publishing a variable at a specified period """
        var.pub_period_ms = period_ms
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_PUB_START]
        data.append(int(period_ms / 15) & 0xFF)
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))

    def pubVarStop(self, var: DAQVariable):
        """ Requests to stop publishing a variable """
        var.pub_period_ms = 0
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_PUB_STOP]
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))

    def handleDaqMsg(self, msg: can.Message):
        """ Interprets and runs commands from DAQ message """
        # Return if not a DAQ message
        if (msg.arbitration_id >> 6) & 0xFFFFF != 0xFFFFF: return

        dbc_msg = self.can_bus.db.get_message_by_frame_id(msg.arbitration_id)
        node_name = dbc_msg.senders[0]
        data = int.from_bytes(msg.data, "little")

        curr_bit = 0
        while (curr_bit <= msg.dlc * 8 - DAQ_CMD_LENGTH - DAQ_ID_LENGTH):
            cmd = (data >> curr_bit) & DAQ_CMD_MASK
            curr_bit += DAQ_CMD_LENGTH

            if cmd == DAQ_RPLY_READ or cmd == DAQ_RPLY_PUB:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                var = list(utils.signals['Main'][node_name][dbc_msg.name].values())[id]
                if not (cmd == DAQ_RPLY_PUB and self.can_bus.is_paused):
                    var.update((data >> curr_bit) & ~(0xFFFFFFFFFFFFFFFF << var.bit_length), msg.timestamp)
                curr_bit += var.bit_length
            elif cmd == DAQ_RPLY_SAVE:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                if self.last_save_request_id == id:
                    self.save_in_progress = False 
                    self.save_in_progress_sig.emit(False)
            elif cmd == DAQ_RPLY_READ_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                print(msg)
                utils.log_error(f"Failed to read {list(utils.signals['Main'][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_WRITE_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to write to {list(utils.signals['Main'][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_SAVE_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to save {list(utils.signals['Main'][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_LOAD_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to load {list(utils.signals['Main'][node_name][dbc_msg.name])[id]}")

    def updateVarDict(self, daq_config: dict):
        """ Creates dictionary of variable objects from daq configuration"""
        for bus in daq_config['busses']:
            # create bus keys
            if bus['bus_name'] not in utils.signals: utils.signals[bus['bus_name']] = {}
            for node in bus['nodes']:
                # create node keys
                if node['node_name'] not in utils.signals[bus['bus_name']]: utils.signals[bus['bus_name']][node['node_name']] = {}
                if f"daq_response_{node['node_name'].upper()}" not in utils.signals[bus['bus_name']][node['node_name']]: utils.signals[bus['bus_name']][node['node_name']][f"daq_response_{node['node_name'].upper()}"] = {}
                id_counter = 0
                for var in node['variables']:
                    # create new variable
                    utils.signals[bus['bus_name']][node['node_name']][f"daq_response_{node['node_name'].upper()}"][var['var_name']] = DAQVariable(
                                   bus['bus_name'], node['node_name'], f"daq_response_{node['node_name'].upper()}", var['var_name'], id_counter, 
                                   var['read_only'], var['bit_length'], "eeprom" in var)
                    id_counter += 1