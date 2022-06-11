import math
from PyQt5 import QtWidgets, QtCore
from ui.cellView import Ui_cellViewer
from communication.can_bus import CanBus
import numpy as np
import can
import utils
import threading

from utils import log_warning

class CellViewer(QtWidgets.QWidget):
    """ Widget that displays battery cell status """

    data_lock = threading.Lock()

    def __init__(self, bus: CanBus, parent=None):
        super(CellViewer, self).__init__(parent)
        self.ui = Ui_cellViewer()
        self.ui.setupUi(self)

        # Configure Horizontal Headers
        self.ui.msgTable.setColumnCount(8)
        self.ui.msgTable.setHorizontalHeaderLabels(["Cell", "Module 1", 
                         "Cell", "Module 2", "Cell", "Module 3", "Cell", "Module 4"])
        header = self.ui.msgTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)

        # Disable ability to edit cells
        self.ui.msgTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)


        self.num_cells = 80
        self.num_modules = 4

        self.ui.msgTable.setRowCount(int(self.num_cells / self.num_modules))

        # Set cell numbers
        for cell in range(self.num_cells):
            self.ui.msgTable.setItem(cell % (self.num_cells / self.num_modules), 
                                     math.floor(cell / (self.num_cells / self.num_modules)) * 2, 
                                     QtWidgets.QTableWidgetItem(str(cell + 1)))

        self.cell_volts = np.zeros(self.num_cells)

        self.fps = 15
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateRows)
        self.timer.start(int(1000.0/self.fps))

        self.sigs_exist = False
        try:
            self.mux_sig = utils.signals['Main']['Precharge']['cell_info']['idx']
            self.cell1 = utils.signals['Main']['Precharge']['cell_info']['v1']
            self.cell2 = utils.signals['Main']['Precharge']['cell_info']['v2']
            self.cell3 = utils.signals['Main']['Precharge']['cell_info']['v3']
            self.cell3.connect(self.messageReceived)
            self.sigs_exist = True
        except:
            utils.log_error("Cell info message not detected, cell viewer will be disabled.")


    def messageReceived(self):
        """ Updates cells based on message contents """
        if self.sigs_exist:
            idx = self.mux_sig.curr_val    
            with self.data_lock:
                self.cell_volts[idx]     = self.cell1.curr_val
                self.cell_volts[idx + 1] = self.cell2.curr_val
                self.cell_volts[idx + 2] = self.cell3.curr_val


    def updateRows(self):
        """ Updates all cells, called periodically """
        if (self.sigs_exist):
            with self.data_lock:
                for cell in range(self.num_cells):
                    self.ui.msgTable.setItem(cell % (self.num_cells / self.num_modules), 
                                            math.floor(cell / (self.num_cells / self.num_modules)) * 2 + 1, 
                                            QtWidgets.QTableWidgetItem(str(self.cell_volts[cell])))
                    self.ui.avgV.setText(str(np.mean(self.cell_volts)))
                    self.ui.maxV.setText(str(np.max(self.cell_volts)))
                    self.ui.minV.setText(str(np.min(self.cell_volts)))
        else:
            for cell in range(self.num_cells):
                self.ui.msgTable.setItem(cell % (self.num_cells / self.num_modules), 
                                        math.floor(cell / (self.num_cells / self.num_modules)) * 2 + 1, 
                                        QtWidgets.QTableWidgetItem('Error'))
