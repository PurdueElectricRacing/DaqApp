from PyQt5 import QtWidgets
from ui.frameViewer import Ui_frameViewer
from communication.can_bus import CanBus
import can

class FrameViewer(QtWidgets.QWidget):
    """ Widget that displays can message data in a table """

    def __init__(self, bus: CanBus, parent=None):
        super(FrameViewer, self).__init__(parent)
        self.ui = Ui_frameViewer()
        self.ui.setupUi(self)

        # Configure Horizontal Headers
        self.ui.msgTable.setColumnCount(7)
        self.ui.msgTable.setHorizontalHeaderLabels(["Timestamp", "Rx/Tx","ID","Sender","Name","DLC","Data"])
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

        self.row_ids = []
        self.row_times = []

    def messageReceived(self, msg: can.Message):
        """ Receives message and adds to row """
        # Try to decode message
        try:
            dbc_msg = self.bus.db.get_message_by_frame_id(msg.arbitration_id)
            try:
                data = str(self.bus.db.decode_message(msg.arbitration_id, msg.data))
            except ValueError:
                data = hex(int.from_bytes(msg.data, "little"))
        except KeyError:
            return

        # Create new row if not yet existing
        if msg.arbitration_id not in self.row_ids:
            self.row_ids.append(msg.arbitration_id)
            self.row_times.append(msg.timestamp)
            self.ui.msgTable.setRowCount(len(self.row_ids))
        row_idx = self.row_ids.index(msg.arbitration_id)

        # Organize row data
        self.row_times[row_idx] = msg.timestamp
        row = [
            f"{(msg.timestamp - self.row_times[row_idx]):.4f}",
            "Rx" if msg.is_rx else "Tx",
            hex(msg.arbitration_id),
            dbc_msg.senders[0],
            dbc_msg.name,
            str(msg.dlc),
            data
        ]
        # Add row entries column by column
        for n, item in enumerate(row):
            self.ui.msgTable.setItem(row_idx, n, QtWidgets.QTableWidgetItem(item))

    def removeRow(self, row_idx: int):
        """ removes row from the table """
        self.row_ids.pop(row_idx)
        self.row_times.pop(row_idx)
        self.ui.msgTable.removeRow(row_idx)