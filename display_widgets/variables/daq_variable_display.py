from PyQt5 import QtWidgets, QtGui, QtCore
from communication.can_bus import BusSignal
from ui.variable import Ui_variableDisplay
import utils
from display_widgets.variables.variable_display import VariableDisplay
import time

DAQ_WRITE_TIMEOUT_MS = 1000
DAQ_READ_TIMEOUT_MS = 1000
DAQ_PERIODIC_READ_MS = 5000


class DAQVariableDisplay(VariableDisplay):
    """ Used to display a DAQ variable with name and units """

    def __init__(self, parent=None):
        super(DAQVariableDisplay, self).__init__(parent)
        self.sig = None
        self.write_in_progress = False
        self.write_timer = QtCore.QTimer()
        self.write_timer.timeout.connect(self.writeTimeout)
        self.read_in_progress = False
        self.read_timer = QtCore.QTimer()
        self.read_timer.timeout.connect(self.readTimeout)
        self.new_value = 0

    def setText(self, txt):
        """ Search for bus signal based on format
            Node.Msg.Variable"""
        parts = txt.split('.')
        try:
            sig = utils.signals[utils.b_str][parts[0]][parts[1]][parts[2]]
        except:
            utils.log_error(f"Invalid DAQ var for variable display: {txt}")
            self.setValue(f"ERROR loading: {txt}")
            return

        self.ui.Value.setReadOnly(sig.read_only)
        if not sig.read_only:
            self.ui.Value.returnPressed.connect(self.writeToVar)

        sig.connect(self.handleReceive)

        self.setName(sig.signal_name)
        self.setUnits(sig.unit)
        self.setValue("Stale")
        self.ui.Name.setToolTip(f"Signal: {sig.signal_name}\n{sig.sig_desc}\nSend type: {sig.send_dtype}, Store type: {sig.store_dtype}\nSender: {sig.node_name}, {sig.message_name}\n{sig.msg_desc}")
        self.ui.Name.setToolTipDuration(-1)
        self.sig = sig

    def writeToVar(self):
        """ Assumes only called if daq var is write enabled """
        txt = self.ui.Value.text()

        try:
            new_value = float(self.ui.Value.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Write Error", "Write failed. Please enter an number")
            return
        if not self.sig.valueSendable(new_value):
            self.ui.Value.setText(str(new_value) + f" <- Invalid for send dtype: {str(self.sig.send_dtype)}, scale: {self.sig.scale}, offset: {self.sig.offset})")
            return
        
        # truncate if necessary
        self.new_value = self.sig.getSendValue(new_value)

        self.ui.Value.setReadOnly(True)
        self.ui.Value.setDisabled(True)
        self.ui.Value.setText(f"W: {str(self.new_value)}")

        self.write_in_progress = True
        utils.daqProt.writeVar(self.sig, self.new_value)
        utils.daqProt.readVar(self.sig)
        self.write_timer.start(DAQ_WRITE_TIMEOUT_MS)

    def writeTimeout(self):
        self.write_timer.stop()
        self.ui.Value.setText(f"W T-Out: {self.new_value}")
        self.ui.Value.setReadOnly(False)
        self.ui.Value.setDisabled(False)
        self.write_in_progress = False

    def handleReceive(self):

        if self.write_in_progress:
            self.write_timer.stop()
            if abs(self.sig.curr_val - self.new_value) > 0.00001:
                self.ui.Value.setText(f"E: New: {self.new_value} != Cur: {self.sig.curr_val}")
            else:
                self.ui.Value.setText(f"{self.new_value}")
            self.ui.Value.setReadOnly(False)
            self.ui.Value.setDisabled(False)
            self.write_in_progress = False
        else:
            self.read_timer.stop()
            if not self.sig.read_only and not self.ui.Value.hasFocus():
                self.ui.Value.setText(str(self.sig.curr_val))
        self.read_in_progress = False

    def readTimeout(self):
        self.read_timer.stop()
        self.read_in_progress = False
        self.setValue("Stale")

    def updatePeriodic(self):
        if not self.sig: return
        # if self.sig.is_stale:
        #     self.setValue("Stale")
        #     self.setEnabled(False)
        # else:
        #     self.setValue(self.sig.curr_val)
        #     self.setEnabled(True)
        if ((time.time() - self.sig.stale_timestamp) * 1000 > DAQ_PERIODIC_READ_MS or 
             self.ui.Value.text() == "Stale") and not self.read_in_progress:
            self.read_timer.start(DAQ_READ_TIMEOUT_MS)
            self.read_in_progress = True
            utils.daqProt.readVar(self.sig)

        if (self.sig.isDirty()): self.ui.Value.setStyleSheet("background:rgb(255, 255, 127);\n")
        else: self.ui.Value.setStyleSheet("background:rgb(255, 255, 255);\n")

        return super().updatePeriodic()
    

    # TODO: stale checking
    # TODO: display update timer based on parent widget