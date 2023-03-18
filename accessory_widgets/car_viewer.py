import math
from PyQt5 import QtWidgets, QtCore
from ui.carView import Ui_carViewer
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning
from accessory_widgets.accessory_widget import AccessoryWidget

class CarViewer(AccessoryWidget):
    """ Widget that displays car status """

    def __init__(self, bus: CanBus, parent=None):
        super(CarViewer, self).__init__(parent)
        self.ui = Ui_carViewer()
        self.ui.setupUi(self)