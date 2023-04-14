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


"""
TODO: parsing, import file vars as signals
        load and save commands are now different
        when you write to a file variable, mark the file as dirty
"""


class DAQVariable(BusSignal):
    """ DAQ variable that can be subscribed (connected) to for receiving updates"""


    def __init__(self, bus_name, node_name, msg_name, sig_name, id, read_only, bit_length, 
                 dtype, store_dtype=None, unit="", msg_desc="", sig_desc="", msg_period=0, file_name=None, file_lbl=None, scale=1, offset=0):
        super(DAQVariable, self).__init__(bus_name, node_name, msg_name, sig_name, dtype, store_dtype=store_dtype, 
                                          unit=unit, msg_desc=msg_desc, sig_desc=sig_desc, msg_period=msg_period)
        self.id = id
        self.read_only = read_only
        self.bit_length = bit_length
        self.file = file_name
        self.file_lbl = file_lbl
        self.pub_period_ms = 0

        self.scale = scale
        self.offset = offset

        self.is_dirty = False

    def fromDAQVar(id, var, node, bus):
        send_dtype = utils.data_types[var['type']]
        # If there is scaling going on, don't store as an integer on accident
        if ('scale' in var and var['scale'] != 1) or ('offset' in var and var['offset'] != 0):
            parse_dtype = utils.data_types['float']
        else:
            parse_dtype = send_dtype
        # Calculate bit length
        bit_length = utils.data_type_length[var['type']]
        if ('length' in var):
            if ('uint' not in var['type'] or var['length'] > bit_length):
                utils.log_error(f"Invalid bit length defined for DAQ variable {var['var_name']}")
            bit_length = var['length']

        return DAQVariable(bus['bus_name'], node['node_name'], f"daq_response_{node['node_name'].upper()}", var['var_name'],
                         id, var['read_only'], bit_length,
                         send_dtype, store_dtype=parse_dtype,
                         unit=(var['unit'] if 'unit' in var else ""),
                         
                         sig_desc=(var['var_desc'] if 'var_desc' in var else ""), 
                         scale=(var['scale'] if 'scale' in var else 1),
                         offset=(var['offset'] if 'offset' in var else 0))
    
    def fromDAQFileVar(id, var, file_name, file_lbl, node, bus):
        send_dtype = utils.data_types[var['type']]
        # If there is scaling going on, don't store as an integer on accident
        if ('scale' in var and var['scale'] != 1) or ('offset' in var and var['offset'] != 0):
            parse_dtype = utils.data_types['float']
        else:
            parse_dtype = send_dtype
        # Calculate bit length
        bit_length = utils.data_type_length[var['type']]

        return DAQVariable(bus['bus_name'], node['node_name'], f"daq_response_{node['node_name'].upper()}", var['var_name'],
                         id, False, bit_length,
                         send_dtype, store_dtype=parse_dtype,
                         unit=(var['unit'] if 'unit' in var else ""),
                         sig_desc=(var['var_desc'] if 'var_desc' in var else ""),
                         file_name=file_name, file_lbl=file_lbl,
                         scale=(var['scale'] if 'scale' in var else 1),
                         offset=(var['offset'] if 'offset' in var else 0))

    def update(self, bytes, timestamp, record):
        val = np.frombuffer(bytes.to_bytes((self.bit_length + 7)//8, 'little'), dtype=self.send_dtype, count=1)
        val = val * self.scale + self.offset
        return super().update(val, timestamp, record)

    def reverseScale(self, val):
        return (val - self.offset) / self.scale

    def valueSendable(self, val):
        # TODO: check max and min from json config
        val = self.reverseScale(val)
        if 'uint' in str(self.send_dtype):
            max_size = pow(2, self.bit_length) - 1
            if val > max_size or val < 0:
                return False
        elif 'int' in str(self.send_dtype):
            s = np.iinfo(self.send_dtype)
            if val < s.min or val > s.max:
                return False
        return True

    def reverseToBytes(self, val):
        if not self.valueSendable(val): return False # Value will not fit in the given dtype
        return (np.array([self.reverseScale(val)], dtype=self.send_dtype).tobytes())

    def getSendValue(self, val):
        if not self.valueSendable(val): return False # Value will not fit in the given dtype
        # Convert to send
        a = np.array([self.reverseScale(val)], dtype=self.send_dtype)[0]
        # Convert back
        return a * self.scale + self.offset

    def isDirty(self):
        if self.file_lbl == None: return False
        return self.is_dirty

    def updateDirty(self, dirty):
        if self.file_lbl == None: return
        self.is_dirty = dirty


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
        utils.daqProt = self

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
        bytes = var.reverseToBytes(new_val)
        # LSB, add variable data to byte array
        for i in range(math.ceil(var.bit_length / 8)):
            data.append(bytes[i])
        var.updateDirty(True)

        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))
        
    def saveFile(self, var: DAQVariable):
        """ Saves variable state in eeprom, expects save complete reply """
        if var.file_lbl == None:
            utils.log_error(f"Invalid save var operation for {var.signal_name}")
            return
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_SAVE]
        lbl = var.file_lbl
        data.append(ord(lbl[0]))
        data.append(ord(lbl[1]))
        data.append(ord(lbl[2]))
        data.append(ord(lbl[3]))
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                        is_extended_id=True,
                                        data=data))
        self.setFileClean(var)
        # self.save_in_progress = True
        # self.last_save_request_id = var.id
        # self.save_in_progress_sig.emit(True)

    def loadFile(self, var: DAQVariable):
        """ Loads a variable from eeprom, cannot be performed during save operation """
        if var.file_lbl == None:
            utils.log_error(f"Invalid load var operation for {var.signal_name}")
            return
        # if self.save_in_progress:
        #     utils.log_error(f"Cannot load var during save operation ")
        #     return
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_LOAD]
        lbl = var.file_lbl
        data.append(ord(lbl[0]))
        data.append(ord(lbl[1]))
        data.append(ord(lbl[2]))
        data.append(ord(lbl[3]))
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id, 
                                         is_extended_id=True,
                                         data=data))
        self.setFileClean(var)

    def pubVar(self, var: DAQVariable, period_ms):
        """ Requests to start publishing a variable at a specified period """
        var.pub_period_ms = period_ms
        dbc_msg = self.can_bus.db.get_message_by_name(f"daq_command_{var.node_name.upper()}")
        data = [((var.id & DAQ_ID_MASK) << DAQ_CMD_LENGTH) | DAQ_CMD_PUB_START]
        data.append(int(period_ms / 15) & 0xFF)
        self.can_bus.sendMsg(can.Message(arbitration_id=dbc_msg.frame_id,
                                         is_extended_id=True,
                                         data=data))

    def forceFault(self, id, state):
        print(f"Id: {id}, State: {state}")
        fault_msg = self.can_bus.db.get_message_by_name(f"set_fault")
        data = fault_msg.encode({"id": id, "value": state})
        self.can_bus.sendMsg(can.Message(arbitration_id=fault_msg.frame_id,
                                        is_extended_id=True,
                                        data=data))

    def create_ids(self, fault_config):
       num = 0
       idx = 0
       for node in fault_config['modules']:
           for fault in node['faults']:
               #id : Owner (MCU) = 4 bits, Index in fault array = 12 bits
               id = ((num << 12) | (idx & 0x0fff))
               # print(hex(id))
               fault['id'] =  id
               idx += 1
           num += 1
       id = 0
       for node in fault_config['modules']:
           node['name_interp'] = id
           id += 1
       for node in fault_config['modules']:
           try:
               node['can_name']
           except KeyError:
               node['can_name'] = node['node_name']
           except:
               print("An error occured configuring a node.")
       return fault_config

    def unforceFault(self, id):
        print(f"Id: {id}. Returning control!")
        fault_msg = self.can_bus.db.get_message_by_name(f"return_fault_control")
        data = fault_msg.encode({"id": id})
        self.can_bus.sendMsg(can.Message(arbitration_id=fault_msg.frame_id,
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
    
    def setFileClean(self, var_in_file: DAQVariable):
        """ Sets all variables in a file to clean (usually after flushing) """
        if (var_in_file.file_lbl == None): return
        node_d = utils.signals[var_in_file.bus_name][var_in_file.node_name]
        contents = node_d['files'][var_in_file.file]['contents']
        vars = node_d[var_in_file.message_name]
        for file_var in contents:
            vars[file_var].updateDirty(False)


    def setFileClean(self, var_in_file: DAQVariable):
        """ Sets all variables in a file to clean (usually after flushing) """
        if (var_in_file.file_lbl == None): return
        node_d = utils.signals[var_in_file.bus_name][var_in_file.node_name]
        contents = node_d['files'][var_in_file.file]['contents']
        vars = node_d[var_in_file.message_name]
        for file_var in contents:
            vars[file_var].updateDirty(False)


    def handleDaqMsg(self, msg: can.Message):
        """ Interprets and runs commands from DAQ message """
        # Return if not a DAQ message
        if (msg.arbitration_id >> 6) & 0xFFFFF != 0xFFFFF: return

        utils.log_error("DAQ MESSAGE")
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
                var = list(utils.signals[utils.b_str][node_name][dbc_msg.name].values())[id]
                if not (cmd == DAQ_RPLY_PUB and self.can_bus.is_paused):
                    var.update((data >> curr_bit) & ~(0xFFFFFFFFFFFFFFFF << var.bit_length), msg.timestamp, not utils.logging_paused)
                    utils.log_error("Updated " + var.signal_name)
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
                utils.log(msg)
                utils.log_error(f"Failed to read {list(utils.signals[utils.b_str][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_WRITE_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to write to {list(utils.signals[utils.b_str][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_SAVE_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to save {list(utils.signals[utils.b_str][node_name][dbc_msg.name])[id]}")
            elif cmd == DAQ_RPLY_LOAD_ERROR:
                id = (data >> curr_bit) & DAQ_ID_MASK
                curr_bit += DAQ_ID_LENGTH
                utils.log_error(f"Failed to load {list(utils.signals[utils.b_str][node_name][dbc_msg.name])[id]}")

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
                    utils.signals[bus['bus_name']][node['node_name']][f"daq_response_{node['node_name'].upper()}"][var['var_name']] = DAQVariable.fromDAQVar(
                        id_counter, var, node, bus)
                    id_counter += 1
                # Check file variables
                if 'files' in node:
                    if 'files' not in utils.signals[bus['bus_name']][node['node_name']]: utils.signals[bus['bus_name']][node['node_name']]['files'] = {}
                    # file_name:is_dirty
                    file_dict = utils.signals[bus['bus_name']][node['node_name']]['files']
                    for file in node['files']:
                        file_dict[file['name']] = {}
                        file_dict[file['name']]['contents'] = []
                        for var in file['contents']:
                            file_dict[file['name']]['contents'].append(var['var_name'])
                            utils.signals[bus['bus_name']][node['node_name']][f"daq_response_{node['node_name'].upper()}"][var['var_name']] = DAQVariable.fromDAQFileVar(
                                id_counter, var, file['name'], file['eeprom_lbl'], node, bus)
                            id_counter += 1
