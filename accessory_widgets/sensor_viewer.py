import math
from PyQt5 import QtWidgets, QtCore
from ui.sensorView import Ui_sensorView
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning
from accessory_widgets.accessory_widget import AccessoryWidget

class SensorViewer(AccessoryWidget):
    """ Widget that displays sensor status """

    def __init__(self, bus: CanBus, parent=None):
        super(SensorViewer, self).__init__(parent)
        self.ui = Ui_sensorView()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.cal_steer_btn.clicked.connect(self.calSteer)

    def calSteer(self):
        """ Zeros the steering angle sensor """
        utils.daqProt.readVar(utils.signals["Main"]["Main_Module"]["daq_response_MAIN_MODULE"]["cal_steer_angle"]) 