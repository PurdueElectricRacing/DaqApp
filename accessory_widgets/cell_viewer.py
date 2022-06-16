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
        self.ui.msgTable.setHorizontalHeaderLabels(["", "Module 1", 
                         "", "Module 2", "", "Module 3", "", "Module 4"])
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

        self.ui.msgTable.setRowCount(int(self.num_cells / self.num_modules) + 1)

        # Set cell numbers
        for cell in range(self.num_cells):
            self.ui.msgTable.setItem(cell % (self.num_cells / self.num_modules) + 1, 
                                     math.floor(cell / (self.num_cells / self.num_modules)) * 2, 
                                     QtWidgets.QTableWidgetItem(str(cell + 1)))
        # Set temp labels
        self.ui.msgTable.setItem(0, 0, QtWidgets.QTableWidgetItem('Avg Tmp'))
        self.ui.msgTable.setItem(0, 2, QtWidgets.QTableWidgetItem('Avg Tmp'))
        self.ui.msgTable.setItem(0, 4, QtWidgets.QTableWidgetItem('Avg Tmp'))
        self.ui.msgTable.setItem(0, 6, QtWidgets.QTableWidgetItem('Avg Tmp'))

        self.cell_volts = np.zeros(self.num_cells)

        self.fps = 10
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
            self.totalV = utils.signals['Main']['Precharge']['battery_info']['voltage']
            self.maxT = utils.signals['Main']['Precharge']['max_cell_temp']['max_temp']
            self.cell1T = utils.signals['Main']['Precharge']['mod_cell_temp_avg']['temp_A']
            self.cell2T = utils.signals['Main']['Precharge']['mod_cell_temp_avg']['temp_B']
            self.cell3T = utils.signals['Main']['Precharge']['mod_cell_temp_avg']['temp_C']
            self.cell4T = utils.signals['Main']['Precharge']['mod_cell_temp_avg']['temp_D']
            self.sigs_exist = True
        except:
            utils.log_error("Cell info message not detected, cell viewer will be disabled.")


    def messageReceived(self):
        """ Updates cells based on message contents """
        if self.sigs_exist:
            idx = self.mux_sig.curr_val    
            with self.data_lock:
                self.cell_volts[idx]     = self.cell1.curr_val / 10000
                self.cell_volts[idx + 1] = self.cell2.curr_val / 10000
                self.cell_volts[idx + 2] = self.cell3.curr_val / 10000


    def updateRows(self):
        """ Updates all cells, called periodically """
        if (self.sigs_exist):
            with self.data_lock:
                for cell in range(self.num_cells):
                    self.ui.msgTable.setItem((cell % (self.num_cells / self.num_modules)) + 1, 
                                            math.floor(cell / (self.num_cells / self.num_modules)) * 2 + 1, 
                                            QtWidgets.QTableWidgetItem(str(self.cell_volts[cell])))
                    self.ui.avgV.setText(str(round(np.mean(self.cell_volts), 2)))
                    self.ui.maxV.setText(str(np.max(self.cell_volts)))
                    self.ui.minV.setText(str(np.min(self.cell_volts)))
            self.ui.msgTable.setItem(0, 1, QtWidgets.QTableWidgetItem(str(self.cell1T.curr_val)))
            self.ui.msgTable.setItem(0, 3, QtWidgets.QTableWidgetItem(str(self.cell2T.curr_val)))
            self.ui.msgTable.setItem(0, 5, QtWidgets.QTableWidgetItem(str(self.cell3T.curr_val)))
            self.ui.msgTable.setItem(0, 7, QtWidgets.QTableWidgetItem(str(self.cell4T.curr_val)))
            self.ui.totalV.setText(str(self.totalV.curr_val))
            self.ui.maxT.setText(str(self.maxT.curr_val))


                
        else:
            for cell in range(self.num_cells):
                self.ui.msgTable.setItem(cell % (self.num_cells / self.num_modules) + 1, 
                                        math.floor(cell / (self.num_cells / self.num_modules)) * 2 + 1, 
                                        QtWidgets.QTableWidgetItem('Error'))
