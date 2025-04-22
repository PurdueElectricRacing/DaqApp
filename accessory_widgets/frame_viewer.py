import string
from PyQt5 import QtWidgets, QtCore
from ui.frameViewer import Ui_frameViewer
from communication.can_bus import CanBus
import can
import threading

from utils import log_warning

class FrameViewer(QtWidgets.QWidget):
    """ Widget that displays can message data in a table """

    data_lock = threading.Lock()

    def __init__(self, bus: CanBus, parent=None):
        super(FrameViewer, self).__init__(parent)
        self.ui = Ui_frameViewer()
        self.ui.setupUi(self)

        # Configure Horizontal Headers
        self.ui.msgTable.setColumnCount(7)
        self.ui.msgTable.setHorizontalHeaderLabels(["Time Delta", "Rx/Tx","ID","Sender","Name","DLC","Data"])
        header = self.ui.msgTable.horizontalHeader()
        # Allowing this to dynamically resize will cause slight performance issues due to update rate
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        # Updated infrequently enough to not need to worry
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        # Data is important enough to justify frequent changes
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)

        # Configure Vertical Headers
        self.ui.msgTable.verticalHeader().sectionDoubleClicked.connect(self.refreshScreen)

        # Disable ability to edit cells
        self.ui.msgTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.ui.msgTable.setSortingEnabled(False)

        self.bus = bus
        bus.new_msg_sig.connect(self.messageReceived)

        self.fps = 15
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateRows)
        self.timer.start(int(1000.0/self.fps))

        self.messages = {}
        self.curr_row_idx = 0


    def messageReceived(self, msg: can.Message):
        """ Receives message and adds to row """
        # Try to decode message
        try:
            dbc_msg = self.bus.db.get_message_by_frame_id(msg.arbitration_id)
            try:
                #decode_msg = self.bus.db.decode_message(msg.arbitration_id, msg.data)
                decode_msg = dbc_msg.decode(msg.data)
                data = ""
                for idx, sig in enumerate(decode_msg):
                    if (type(decode_msg[sig]) == str):
                        data += str(sig)+": "+decode_msg[sig]+" "+(dbc_msg.signals[idx].unit if dbc_msg.signals[idx].unit else "")+", "
                    elif (dbc_msg.name == 'uds_command_daq'):
                        data = hex(int.from_bytes(msg.data, "big"))
                    else:
                        data += str(sig)+": "+"{:.3f}".format(decode_msg[sig])+" "+(dbc_msg.signals[idx].unit if dbc_msg.signals[idx].unit else "")+", "
            except ValueError as e:
                data = hex(int.from_bytes(msg.data, "little"))
                if "daq" not in dbc_msg.name:
                    log_warning(e)
        except KeyError:
            return

        with self.data_lock:
            # Create new row if not yet existing
            if dbc_msg.name not in self.messages:
                self.messages[dbc_msg.name] = {'id': msg.arbitration_id, 'time': msg.timestamp, 'delta': 0, 'dlc': msg.dlc, 'data': data, 'raw_data': msg.data, 'row_idx': self.curr_row_idx, 'old_data': msg.data, 'old_dlc': msg.dlc, 'old_delta': 0}
                # We just added a row so increment our new row counter
                self.curr_row_idx += 1
                self.ui.msgTable.setRowCount(self.curr_row_idx)

                # update row contents that do not change for a message once
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 1, QtWidgets.QTableWidgetItem("Rx" if msg.is_rx else "Tx"))
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 2, QtWidgets.QTableWidgetItem(hex(msg.arbitration_id)))
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 3, QtWidgets.QTableWidgetItem(dbc_msg.senders[0]))
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 4, QtWidgets.QTableWidgetItem(dbc_msg.name))

                # Create item objects for the new rows to update periodically
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 0, QtWidgets.QTableWidgetItem("0")) # Just recieved the item we have no valid delta
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 5, QtWidgets.QTableWidgetItem(str(msg.dlc)))
                self.ui.msgTable.setItem(self.messages[dbc_msg.name]['row_idx'], 6, QtWidgets.QTableWidgetItem(data))

            else:
                self.messages[dbc_msg.name]['delta'] = msg.timestamp - self.messages[dbc_msg.name]['time']
                self.messages[dbc_msg.name]['time'] = msg.timestamp
                self.messages[dbc_msg.name]['dlc'] = msg.dlc
                self.messages[dbc_msg.name]['data'] = data
                # Avoid costly string comparison
                self.messages[dbc_msg.name]['raw_data'] = msg.data


    def updateRows(self):
        """ Updates all rows, called periodically """
        # Handle the updates in one batch to avoid sending too many requests to UI
        self.ui.msgTable.setUpdatesEnabled(False)
        with self.data_lock:
            for idx, msg in enumerate(self.messages):
                # Only update the delta if it has actually changed
                if (self.messages[msg]['old_delta'] != self.messages[msg]['delta']):
                  self.ui.msgTable.item(idx, 0).setText(f"{self.messages[msg]['delta']:.4f}")
                  self.messages[msg]['old_delta'] = self.messages[msg]['delta']

                # Only update the DLC if it has changed
                if (self.messages[msg]['old_dlc'] != self.messages[msg]['dlc']):
                  self.ui.msgTable.item(idx, 5).setText(str(self.messages[msg]['dlc']))
                  self.messages[msg]['old_dlc'] = self.messages[msg]['dlc']

                # Only update the data if it has changed
                if (self.messages[msg]['old_data'] != self.messages[msg]['raw_data']):
                    self.ui.msgTable.item(idx, 6).setText(self.messages[msg]['data'])
                    self.messages[msg]['old_data'] = self.messages[msg]['raw_data']
        # Display batch of updates
        self.ui.msgTable.setUpdatesEnabled(True)
        self.ui.msgTable.viewport().update()


    def refreshScreen(self):
        """ Empties table and allows it to repopulate """
        with self.data_lock:
            for idx, msg in enumerate(self.messages):
              self.ui.msgTable.removeRow(idx)
            self.messages = {}
            self.curr_row_idx = 0
