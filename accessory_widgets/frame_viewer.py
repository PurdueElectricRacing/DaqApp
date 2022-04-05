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
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)

        # Configure Vertical Headers
        self.ui.msgTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.msgTable.verticalHeader().sectionDoubleClicked.connect(self.removeRow)

        # Disable ability to edit cells
        self.ui.msgTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.bus = bus
        bus.new_msg_sig.connect(self.messageReceived)

        self.fps = 15
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateRows)
        self.timer.start(int(1000.0/self.fps))

        self.row_ids = []
        self.row_times = []
        self.row_deltas = []
        self.row_dlcs = []
        self.row_data = []


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
                    else:
                        data += str(sig)+": "+"{:.3f}".format(decode_msg[sig])+" "+(dbc_msg.signals[idx].unit if dbc_msg.signals[idx].unit else "")+", "
            except ValueError as e:
                data = hex(int.from_bytes(msg.data, "little"))
                log_warning(e)
        except KeyError:
            return

        with self.data_lock:
            # Create new row if not yet existing
            if msg.arbitration_id not in self.row_ids:
                self.row_ids.append(msg.arbitration_id)
                self.row_times.append(msg.timestamp)
                self.row_deltas.append(0)
                self.row_dlcs.append(msg.dlc)
                self.row_data.append(data)
                self.ui.msgTable.setRowCount(len(self.row_ids))
                
                # update row contents that do not change for a message once
                self.ui.msgTable.setItem(len(self.row_ids) - 1, 1, QtWidgets.QTableWidgetItem("Rx" if msg.is_rx else "Tx"))
                self.ui.msgTable.setItem(len(self.row_ids) - 1, 2, QtWidgets.QTableWidgetItem(hex(msg.arbitration_id)))
                self.ui.msgTable.setItem(len(self.row_ids) - 1, 3, QtWidgets.QTableWidgetItem(dbc_msg.senders[0]))
                self.ui.msgTable.setItem(len(self.row_ids) - 1, 4, QtWidgets.QTableWidgetItem(dbc_msg.name))
            else:
                row_idx = self.row_ids.index(msg.arbitration_id)
                self.row_deltas[row_idx] = msg.timestamp - self.row_times[row_idx]
                self.row_times[row_idx] = msg.timestamp
                self.row_dlcs[row_idx] = msg.dlc
                self.row_data[row_idx] = data

    def updateRows(self):
        """ Updates all rows, called periodically """
        with self.data_lock:
            for idx in range(len(self.row_ids)):
                self.ui.msgTable.setItem(idx, 0, QtWidgets.QTableWidgetItem(f"{self.row_deltas[idx]:.4f}"))
                self.ui.msgTable.setItem(idx, 5, QtWidgets.QTableWidgetItem(str(self.row_dlcs[idx])))
                self.ui.msgTable.setItem(idx, 6, QtWidgets.QTableWidgetItem(self.row_data[idx]))

    def removeRow(self, row_idx: int):
        """ removes row from the table """
        with self.data_lock:
            self.row_ids.pop(row_idx)
            self.row_times.pop(row_idx)
            self.row_deltas.pop(row_idx)
            self.row_dlcs.pop(row_idx)
            self.row_data.pop(row_idx)
            self.ui.msgTable.removeRow(row_idx)