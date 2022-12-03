import math
from PyQt5 import QtWidgets, QtCore
from ui.chargeView import Ui_chargeViewer
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning
from accessory_widgets.accessory_widget import AccessoryWidget

class ChargeViewer(AccessoryWidget):
    """ Widget that displays charging status """

    def __init__(self, bus: CanBus, parent=None):
        super(ChargeViewer, self).__init__(parent)
        self.ui = Ui_chargeViewer()
        self.ui.setupUi(self)