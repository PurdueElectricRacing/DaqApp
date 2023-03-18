import math
from PyQt5 import QtWidgets, QtCore
from ui.motorViewer import Ui_motorViewer
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning
from accessory_widgets.accessory_widget import AccessoryWidget

class MotorViewer(AccessoryWidget):
    """ Widget that displays motor status """

    def __init__(self, bus: CanBus, parent=None):
        super(MotorViewer, self).__init__(parent)
        self.ui = Ui_motorViewer()
        self.ui.setupUi(self)