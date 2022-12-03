from PyQt5 import QtWidgets, QtGui
from communication.can_bus import BusSignal
from ui.variable import Ui_variableDisplay
import utils
import time
from display_widgets.variables.variable_display import VariableDisplay


class CANVariableDisplay(VariableDisplay):
    """ Used to display a signal from CAN with name and units """

    def __init__(self, parent=None):
        super(CANVariableDisplay, self).__init__(parent)
        self.sig = None

    def setText(self, txt):
        """ Search for bus signal based on format
            Node.Msg.Signal"""
        parts = txt.split('.')
        try:
            sig = utils.signals[utils.b_str][parts[0]][parts[1]][parts[2]]
        except:
            utils.log_error(f"Invalid CAN msg for variable display: {txt}")
            self.setValue(f"ERROR loading: {txt}")
            return

        self.setName(sig.signal_name)
        self.setUnits(sig.unit)
        self.setValue("Stale")
        self.ui.Name.setToolTip(f"Signal: {sig.signal_name}\n{sig.sig_desc}\nSend type: {sig.send_dtype}, Store type: {sig.store_dtype}\nSender: {sig.node_name}, {sig.message_name}\n{sig.msg_desc}")
        self.ui.Name.setToolTipDuration(-1)
        self.sig = sig

    def updatePeriodic(self):
        if not self.sig: return
        if self.sig.is_stale:
            self.setValue(f"Stale: {int(time.time() - self.sig.stale_timestamp)}")
            self.setEnabled(False)
        else:
            self.setValue(self.sig.curr_val)
            self.setEnabled(True)
        return super().updatePeriodic()
    

    # TODO: stale checking
    # TODO: display update timer based on parent widget