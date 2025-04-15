import string
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem
from ui.busSelection import Ui_Dialog
from communication.can_bus import CanBus
from communication.daq_protocol import DaqProtocol
import utils
import json
import can
import threading
import random

class CanBusSelector(QtWidgets.QDialog):
  def __init__(self, instance, base_can_config, parent=None):
        super(CanBusSelector, self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.bus_options = []
        self.can_config = base_can_config
        self.instance = instance

        # Populate values from CAN config
        for bus in base_can_config['busses']:
            self.addStatusIndicator(bus['bus_name'])

        self.exec_()

  def accept(self):
      for idx, bus_option in enumerate(self.bus_options):
        if bus_option.isChecked():
          selected_bus = bus_option.text()
          selected_idx = idx
          print(f"Bus: {selected_bus}, idx: {selected_idx}")
      if 'selected_bus' not in locals():
          print("No bus selected fkn loser")
          return
      self.instance.can_bus.swap_bus(selected_idx)

      super().accept()

  def addStatusIndicator(self, name):
        """Add Radio buttons representing each CAN bus"""
        bus_option = QtWidgets.QRadioButton(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        bus_option.setFont(font)
        bus_option.setAutoExclusive(True)
        bus_option.setChecked(False)
        bus_option.setText(name)
        self.bus_options.append(bus_option)
        self.ui.verticalLayout.insertWidget(len(self.bus_options), bus_option)


  # @staticmethod
  # def setupCanBus(parent=None):
  #     """ Used to edit the preferences (opens dialog) """
  #     CANBusSelector = CanBusSelector(parent=parent)
  #     CANBusSelector.exec_()
