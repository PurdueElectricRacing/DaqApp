import math
from PyQt5 import QtWidgets, QtCore
from ui.systemMonitor import Ui_systemMonitor
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning
from accessory_widgets.accessory_widget import AccessoryWidget

class SystemMonitor(AccessoryWidget):
    """ Widget that displays system status """

    def __init__(self, bus: CanBus, parent=None):
        super(SystemMonitor, self).__init__(parent)
        self.ui = Ui_systemMonitor()
        self.ui.setupUi(self)