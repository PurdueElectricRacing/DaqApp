import string
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem
from ui.faultViewer import Ui_FaultViewer
from communication.can_bus import CanBus
import utils
import json
import can
import threading
import random

class FaultViewer(QtWidgets.QWidget):

    data_lock = threading.Lock()

    def __init__(self, bus: CanBus, faultConfig, parent=None):
        super(FaultViewer, self).__init__(parent)
        self.ui = Ui_FaultViewer()
        self.ui.setupUi(self)


        self.Config = faultConfig
        # self.setupJSON()


        self.ui.NodeSelect.activated.connect(self.selectFault)
        self.ui.MessageSend.clicked.connect(self.sendMessage)

        self.bus = bus
        bus.new_msg_sig.connect(self.messageRecieved)

        self.sigs_exist = False
        self.ui.indicators = []

        self.ui.Zero.setChecked(True)

        self.ui.Info.setColumnCount(2)
        self.ui.Info.setHeaderLabels(["Fault", "Status", "ID"])

        for node in faultConfig['modules']:
            item = QTreeWidgetItem([node['node_name']])
            for fault in node['faults']:
                child = QTreeWidgetItem([fault['fault_name'], 'N/A', hex(fault['id'])])
                item.addChild(child)
            self.ui.Info.addTopLevelItem(item)




        for node in faultConfig['modules']:
            self.ui.NodeSelect.addItem(node['node_name'])
            self.addStatusIndicator(node['node_name'])

        self.selectFault()


        self.fps = 10
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTree)
        self.timer.start(int(1000.0/self.fps))

    def addStatusIndicator(self, name):
        indic = QtWidgets.QRadioButton(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        indic.setFont(font)
        indic.setAutoExclusive(False)
        indic.setChecked(False)
        indic.setText(name)
        self.ui.indicators.append(indic)
        self.ui.nodeStatus.insertWidget(len(self.ui.indicators), indic)

    def selectFault(self):
        self.ui.FaultSelect.clear()
        for node in self.Config['modules']:
            content = self.ui.NodeSelect.currentText()
            if node['node_name'] == content:
                for fault in node['faults']:
                    self.ui.FaultSelect.addItem(fault['fault_name'])

    def sendMessage(self):
        print(f"Message: \nNode: {self.ui.NodeSelect.currentText()}\nFault: {self.ui.FaultSelect.currentText()}")
        if self.ui.Zero.isChecked():
           print("Value: 0")
        else:
           print("Value: 1")

    def updateTree(self):
        return
    def messageRecieved(self, msg: can.Message):
        # Try to decode message
        index = -1
        latched = -1
        foundidx = False
        foundLatch = False
        try:
            dbc_msg = self.bus.db.get_message_by_frame_id(msg.arbitration_id)
            try:
                decode_msg = dbc_msg.decode(msg.data)
                for idx, sig in enumerate(decode_msg):
                    if (type(decode_msg[sig]) != str):
                        if sig == "idx":
                            index = decode_msg[sig]
                            foundidx = True
                        if sig == "latched":
                            latched = decode_msg[sig]
                            foundLatch = True
            except ValueError as e:
                data = hex(int.from_bytes(msg.data, "little"))
                utils.log_warning(e)
        except KeyError:
            return
        with self.data_lock:
            if foundidx and foundLatch:
                for idx1, node in enumerate(self.Config['modules']):
                    for idx2, fault in enumerate(node['faults']):
                        if fault['id'] == index:
                            item = self.ui.Info.topLevelItem(idx1).child(idx2)
                            item.setText(1, (str)(latched))
                            indicator = self.ui.indicators[idx1]
                            indicator.setChecked(True)
                            indicator.show
                foundidx = False
                foundLatch = False
