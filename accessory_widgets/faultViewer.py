import string
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem
from ui.faultViewer import Ui_FaultViewer
from communication.can_bus import CanBus
from communication.daq_protocol import DaqProtocol
import utils
import json
import can
import threading
import random

class FaultViewer(QtWidgets.QWidget):

    data_lock = threading.Lock()

    def __init__(self, bus: CanBus, faultConfig, daq_protocol: DaqProtocol, parent=None):
        super(FaultViewer, self).__init__(parent)
        self.ui = Ui_FaultViewer()
        self.ui.setupUi(self)



        self.Config = faultConfig
        self.daq_protocol = daq_protocol

        #Connect actions
        self.ui.NodeSelect.activated.connect(self.selectFault)
        self.ui.MessageSend.clicked.connect(self.sendMessage)
        self.ui.ReturnSend.clicked.connect(self.returnMessage)

        self.bus = bus
        bus.new_msg_sig.connect(self.messageRecieved)

        self.sigs_exist = False
        self.ui.indicators = []

        self.ui.Zero.setChecked(True)

        #Set up QTreewidget
        self.ui.Info.setColumnCount(2)
        self.ui.Info.setHeaderLabels(["Fault", "Status", "ID"])

        for node in faultConfig['modules']:
            item = QTreeWidgetItem([node['node_name']])
            for fault in node['faults']:
                child = QTreeWidgetItem([fault['fault_name'], 'N/A', hex(fault['id'])])
                item.addChild(child)
            self.ui.Info.addTopLevelItem(item)


        #Setup Status indicators
        self.fps = 10
        self.timer = QtCore.QTimer()

        for node in faultConfig['modules']:
            node['time_since_rx'] = 0
            self.ui.NodeSelect.addItem(node['node_name'])
            self.addStatusIndicator(node['node_name'])

        self.selectFault()



        self.timer.timeout.connect(self.updateTime)
        self.timer.start(int(1000.0/self.fps))

    def addStatusIndicator(self, name):
        """Add Radio buttons representing node status"""
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
        """Populates bottom combobox with faults depending on node in main combobox"""
        self.ui.FaultSelect.clear()
        for node in self.Config['modules']:
            content = self.ui.NodeSelect.currentText()
            if node['node_name'] == content:
                for fault in node['faults']:
                    self.ui.FaultSelect.addItem(fault['fault_name'])

    def sendMessage(self):
        """Generate a CAN message to send to nodes to force a fault"""
        state = 1
        if self.ui.Zero.isChecked():
           print("Value: 0")
           state = 0
        else:
           print("Value: 1")
        for node in self.Config['modules']:
            if ((str)(node['node_name']).lower() == (str)(self.ui.NodeSelect.currentText()).lower()):
                for fault in node['faults']:
                    if ((str)(fault['fault_name']).lower() == (str)(self.ui.FaultSelect.currentText()).lower()):
                        self.daq_protocol.forceFault(fault['id'], state)

    def returnMessage(self):
        """Generate a CAN message to send to nodes to return control of forced faults"""
        for node in self.Config['modules']:
            if ((str)(node['node_name']).lower() == (str)(self.ui.NodeSelect.currentText()).lower()):
                for fault in node['faults']:
                    if ((str)(fault['fault_name']).lower() == (str)(self.ui.FaultSelect.currentText()).lower()):
                        self.daq_protocol.unforceFault(fault['id'])


    def updateTime(self):
        """Make Status radio buttons display the offline nodes, make sure that no stale faults are viewable"""
        for idx, node in enumerate(self.Config['modules']):
            if node['time_since_rx'] > 3:
                self.ui.indicators[idx].setChecked(False)
                for idx2, fault in enumerate(node['faults']):
                    self.ui.Info.topLevelItem(idx).child(idx2).setText(1, "N/A")
            else:
                node['time_since_rx'] += 1

    def messageRecieved(self, msg: can.Message):
        """Decode incoming fault messages, update qTreewidget with correct fault, and
            make sure node status is live"""
        # Try to decode message
        index = -1
        latched = -1
        try:
            dbc_msg = self.bus.db.get_message_by_frame_id(msg.arbitration_id)
            try:
                decode_msg = dbc_msg.decode(msg.data)
                index = decode_msg['idx']
                latched = decode_msg['latched']
            except ValueError as e:
                data = hex(int.from_bytes(msg.data, "little"))
                utils.log_warning(e)
        except KeyError:
            return
        with self.data_lock:
            for idx1, node in enumerate(self.Config['modules']):
                for idx2, fault in enumerate(node['faults']):
                    if fault['id'] == index:
                        item = self.ui.Info.topLevelItem(idx1).child(idx2)
                        item.setText(1, (str)(latched))
                        indicator = self.ui.indicators[idx1]
                        indicator.setChecked(True)
                        node['time_since_rx'] = 0
                        indicator.show
