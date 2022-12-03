import math
from PyQt5 import QtWidgets, QtCore
from ui.chargeView import Ui_chargeViewer
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning

class AccessoryWidget(QtWidgets.QWidget):
    """ Widget that contains variables to display """

    def __init__(self, bus: CanBus, parent=None):
        super(AccessoryWidget, self).__init__(parent)

        self.var_displays = []

        self.fps = 15
        self.var_timer = QtCore.QTimer()
        self.var_timer.timeout.connect(self.updateVariables)

    def show(self) -> None:
        self.var_timer.start(int(1000.0/self.fps))
        return super().show()

    def hide(self) -> None:
        self.var_timer.stop()
        return super().hide()

    def updateVariables(self):
        for var in self.var_displays:
            var.updatePeriodic()

    def registerVariable(self, var):
        self.var_displays.append(var)
