import string
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem
from ui.timeSyncResult import Ui_Dialog
import utils
import json
import can
import threading
import random

class TimeSyncStatus(QtWidgets.QDialog):
  def __init__(self, old_time, new_time, ret_code, parent=None):
        super(TimeSyncStatus, self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        if (ret_code == 5):
          label = QtWidgets.QLabel(f"Failed to establish communication with DAQ PCB.")
          self.ui.verticalLayout_2.insertWidget(1, label)
        elif (ret_code == 4):
          label = QtWidgets.QLabel(f"Lost contact with DAQ PCB during the time sync process.")
          label2 = QtWidgets.QLabel(f"Check bus load/connection integrity.")
          self.ui.verticalLayout_2.insertWidget(1, label)
          self.ui.verticalLayout_2.insertWidget(2, label2)
        elif (ret_code == 1):
          successMsg = QtWidgets.QLabel("Success!")
          old_time_lbl = QtWidgets.QLabel(f"Old Time on DAQ: {old_time}")

          label = QtWidgets.QLabel(f"New time on DAQ: {new_time}")
          self.ui.verticalLayout_2.insertWidget(1, successMsg)
          self.ui.verticalLayout_2.insertWidget(2, old_time_lbl)
          self.ui.verticalLayout_2.insertWidget(3, label)
        else:
          label = QtWidgets.QLabel(f"Uh oh! Time change attempted, but RTC failed to register time change.")
          old_time_lbl = QtWidgets.QLabel(f"Old Time on DAQ: {old_time}")
          label = QtWidgets.QLabel(f"New time on DAQ: {new_time}")
          self.ui.verticalLayout_2.insertWidget(1, successMsg)
          self.ui.verticalLayout_2.insertWidget(2, old_time_lbl)
          self.ui.verticalLayout_2.insertWidget(3, label)

        self.exec_()
