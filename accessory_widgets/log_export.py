from PyQt5 import QtWidgets
from PyQt5.Qt import Qt
from communication.can_bus import BusSignal, CanBus
from ui.logExport import Ui_logExport
import utils
import numpy as np

EXPORT_CHRONOLOGICAL = "chronological"
EXPORT_BINNED = "binned"

class LogExporter(QtWidgets.QWidget):
    """ Log export tool to csv """

    def __init__(self, bus: CanBus, parent=None):
        super(LogExporter, self).__init__(parent=parent)
        self.ui = Ui_logExport()
        self.ui.setupUi(self)
        self.bus = bus

        # Signal connections
        self.ui.saveButton.clicked.connect(self.saveLog)
        self.ui.formatSelectCombo.currentIndexChanged.connect(self.formatChanged)
    
        # Populate with items
        for bus in utils.signals:
            parent = QtWidgets.QTreeWidgetItem(self.ui.signalTree)
            parent.setText(0, bus)
            parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            for node in utils.signals[bus]:
                node_item = QtWidgets.QTreeWidgetItem(parent)
                node_item.setFlags(node_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                node_item.setText(0, node)
                for msg in utils.signals[bus][node]:
                    msg_item = QtWidgets.QTreeWidgetItem(node_item)
                    msg_item.setFlags(msg_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                    msg_item.setText(0, msg)
                    for signal in utils.signals[bus][node][msg]:
                        signal_item = QtWidgets.QTreeWidgetItem(msg_item)
                        signal_item.setFlags(signal_item.flags() | Qt.ItemIsUserCheckable)
                        signal_item.setText(0, signal)
                        signal_item.setCheckState(0, Qt.Unchecked)
        
        self.ui.formatSelectCombo.addItems([EXPORT_CHRONOLOGICAL, EXPORT_BINNED])

        self.checked_sigs = []
        self.export_array = np.array([])
        self.header = ""
        self.bin_size = 15

        self.ui.binSizeSpin.setValue(self.bin_size)
        self.ui.binSizeSpin.hide()
        self.ui.binSizeLabel.hide()
    
    def formatChanged(self):
        if self.ui.formatSelectCombo.currentText() == EXPORT_BINNED:
            self.ui.binSizeSpin.show()
            self.ui.binSizeLabel.show()
        else:
            self.ui.binSizeSpin.hide()
            self.ui.binSizeLabel.hide()
    
    def saveLog(self):
        # extract checked signals
        self.checked_sigs = []
        iterator = QtWidgets.QTreeWidgetItemIterator(self.ui.signalTree, flags=QtWidgets.QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            # only leafs
            if item.childCount() == 0:
                msg = item.parent()
                node = msg.parent()
                bus = node.parent()
                #print(f"bus: {bus.text(0)}, node: {node.text(0)}, msg: {msg.text(0)}, signal: {item.text(0)}")
                self.checked_sigs.append(utils.signals[bus.text(0)][node.text(0)][msg.text(0)][item.text(0)])
            iterator += 1

        format = self.ui.formatSelectCombo.currentText()
        if format == EXPORT_CHRONOLOGICAL: self.exportChronological()
        elif format == EXPORT_BINNED: self.exportBinned()

    def exportChronological(self):
        # create array with columns of time, bus, node, msg, signal name, value
        exp = np.array([])
        self.export_array = np.array([])

        for sig in self.checked_sigs:
            # np.column_stack -> horizontal arrays to vertical columns
            # np.full(A.size, value) -> creates array filled with value
            with sig.data_lock:
                sig_chunk = np.column_stack((sig.times[:sig.length], 
                                             np.full(sig.length, sig.bus_name),
                                             np.full(sig.length, sig.node_name),
                                             np.full(sig.length, sig.message_name),
                                             np.full(sig.length, sig.signal_name),
                                             sig.data[:sig.length]))
                # np.concatenate((), axis=0) -> stacks columns
                if exp.size != 0:
                    exp = np.concatenate((exp, sig_chunk))
                else:
                    exp = sig_chunk
        
        # add events
        exp = np.concatenate((exp, np.column_stack((np.array(utils.events),
                                                    np.full((len(utils.events), 4), "")))))
        # A[np.argsort(A[:,0])] -> sorts by first column
        self.export_array = exp[np.argsort(exp[:,0].astype(np.float))]

        self.header = f"{self.bus.start_date_time_str}, Bus, Node, Message, Signal, Value"

        self.saveArray()

    
    def exportBinned(self):
        # create array with columns of time (bins of bin size), signal 1, ...
        # header will include information about what bus, node, and message the signal belongs to

        signal_time_array = np.array([])
        # combine into mega array like exporting chronologically
        for sig in self.checked_sigs:
            # np.column_stack -> horizontal arrays to vertical columns
            # np.full(A.size, value) -> creates array filled with value
            with sig.data_lock:
                sig_chunk = np.column_stack((sig.times[:sig.length], 
                                             np.full(sig.length, sig.bus_name),
                                             np.full(sig.length, sig.node_name),
                                             np.full(sig.length, sig.message_name),
                                             np.full(sig.length, sig.signal_name),
                                             sig.data[:sig.length]))
                # np.concatenate((), axis=0) -> stacks columns
                if signal_time_array.size != 0:
                    signal_time_array = np.concatenate((signal_time_array, sig_chunk))
                else:
                    signal_time_array = sig_chunk
        
        self.bin_size = self.ui.binSizeSpin.value()
        bins = np.arange(signal_time_array[:,0].astype(np.float).min(), signal_time_array[:, 0].astype(np.float).max()+self.bin_size/1000.0, self.bin_size/1000.0)

        # index of the bin each row belongs to
        bin_locs = np.digitize(signal_time_array[:,0].astype(np.float), bins)

        self.export_array = np.array([])
        self.export_array = np.column_stack((bins, np.full((bins.size, len(self.checked_sigs)), np.inf)))

        col_lookup = {}
        for idx, sig in enumerate(self.checked_sigs):
            if sig.bus_name not in col_lookup: col_lookup[sig.bus_name] = {}
            if sig.node_name not in col_lookup[sig.bus_name]: col_lookup[sig.bus_name][sig.node_name] = {}
            if sig.message_name not in col_lookup[sig.bus_name][sig.node_name]: col_lookup[sig.bus_name][sig.node_name][sig.message_name] = {}
            col_lookup[sig.bus_name][sig.node_name][sig.message_name][sig.signal_name] = idx
            
        # populate data into export array
        for idx, bin_loc in enumerate(bin_locs):
            row = signal_time_array[idx]
            sig_idx = col_lookup[row[1]][row[2]][row[3]][row[4]]
            self.export_array[bin_loc][sig_idx + 1] = row[5]
        
        # check for infs left over for each column, fill in previous value
        for col in range(len(self.checked_sigs)):
            for row in range(len(bins)):
                if(self.export_array[row][col+1] == np.inf):
                    if row == 0: self.export_array[row][col+1] = 0
                    else:
                        self.export_array[row][col+1] = self.export_array[row-1][col+1]

        # Create header for the columns
        bus_row = f"{self.bus.start_date_time_str}"
        node_row = "Node"
        msg_row = "Message"
        sig_row = "Signal"
        for sig in self.checked_sigs:
            bus_row += f", {sig.bus_name}"
            node_row += f", {sig.node_name}"
            msg_row += f", {sig.message_name}"
            sig_row += f", {sig.signal_name}"
        
        sig_row += ", Events: " + str(utils.events)
        
        self.header = "\n".join((bus_row, node_row, msg_row, sig_row))
        self.saveArray()
    
    def saveArray(self):
        file_location, _ = QtWidgets.QFileDialog.getSaveFileName(self, filter="*.csv")
        print(file_location)
        np.savetxt(file_location, self.export_array, delimiter=',', fmt='%s', header=self.header)
    
