from PyQt5 import QtCore
import time

class DAQVariable(QtCore.QObject):
    """ DAQ variable that can be subscribed (connected) to for receiving updates"""
    update_sig = QtCore.pyqtSignal()

    def __init__(self, var_config):
        super(DAQVariable, self).__init__()
        self.curr_val = "None"
        self.last_update_time = 0

        self.id             = var_config['id']
        self.name           = var_config['var_name']
        self.node_name      = var_config['node_name']
        self.bus_name       = var_config['bus_name']
        self.read_only      = var_config['read_only']
        self.bit_length     = var_config['bit_length']
        self.eeprom_enabled = var_config['eeprom_enabled']
        
    def connect(self, func: 'function'):
        self.update_sig.connect(func)
    
    def disconnect(self):
        self.update_sig.disconnect()
    
    def update(self, val):
        self.curr_val = val
        self.last_update_time = time.time()
        self.update_sig.emit()
    
    