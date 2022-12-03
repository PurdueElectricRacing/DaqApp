from PyQt5 import QtWidgets
from ui.variableEditor import Ui_variableEditor
from communication.daq_protocol import DaqProtocol
import utils

# TODO: detect unsaved changes (prevent confusion of thinking save also writes)
class VariableEditor(QtWidgets.QWidget):
    """ Variable editor for modifying DAQ variables over CAN """

    def __init__(self, daq_protocol: DaqProtocol, parent=None):
        super(VariableEditor, self).__init__(parent)
        self.ui = Ui_variableEditor()
        self.ui.setupUi(self)
        self.daq_protocol = daq_protocol

        # Signal connections
        self.daq_protocol.save_in_progress_sig.connect(self.handleSaveProgress)
        self.ui.variableList.itemClicked.connect(self.varSelected)
        self.ui.variableList.itemDoubleClicked.connect(self.varDoubleClicked)
        self.ui.readButton.clicked.connect(self.readButtonClicked)
        self.ui.writeButton.clicked.connect(self.writeButtonClicked)
        self.ui.saveButton.clicked.connect(self.saveButtonClicked)
        self.ui.loadButton.clicked.connect(self.loadButtonClicked)
        self.ui.nodeSelector.currentIndexChanged.connect(self.updateVarList)
        self.ui.startPubButton.clicked.connect(self.startPubButtonClicked)
        self.ui.stopPubButton.clicked.connect(self.stopPubButtonClicked)

        # Disable buttons
        self.ui.readButton.setDisabled(True)
        self.ui.writeButton.setDisabled(True)
        self.ui.saveButton.setDisabled(True)
        self.ui.loadButton.setDisabled(True)
        self.ui.startPubButton.setDisabled(True)
        self.ui.stopPubButton.setDisabled(True)

        # Add nodes to node selector
        self.updateNodeList()

        self.curr_var = None
        self.save_in_prog = False 
        self.changes_unsaved = False

    def updateNodeList(self):
        """ Update the nodes available in the nodeSelector combo box """
        self.ui.nodeSelector.clear()
        self.daq_enabled_nodes = [key for key in utils.signals[utils.b_str].keys() if f"daq_response_{key.upper()}" in utils.signals[utils.b_str][key]]
        self.ui.nodeSelector.addItems(self.daq_enabled_nodes)

    def varSelected(self, item:QtWidgets.QListWidgetItem):
        """ Subscribes to receive updates of the current variable """
        self.ui.selectLbl.setText(f"Editing \"{item.text()}\".")
        self.ui.currValDisp.setText("")
        if self.curr_var: self.curr_var.disconnect(self.handleReceive)
        self.curr_var = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()][f"daq_response_{self.ui.nodeSelector.currentText().upper()}"][
                                          self.ui.variableList.currentItem().text()]
        self.curr_var.connect(self.handleReceive)

        self.ui.pubPeriodDisp.setText(str(self.curr_var.pub_period_ms))

        self.changes_unsaved = False
        self.handleSaveProgress(self.save_in_prog)

        self.ui.readButton.setDisabled(False)
        self.ui.writeButton.setDisabled(self.curr_var.read_only)
        self.ui.saveButton.setDisabled(self.curr_var.file_lbl == None)
        self.ui.loadButton.setDisabled(self.save_in_prog or (self.curr_var.file_lbl == None) or self.curr_var.read_only)
        self.ui.startPubButton.setDisabled(False)
        self.ui.stopPubButton.setDisabled(False)
    
    def varDoubleClicked(self, item):
        """ Selects and reads from variable """
        self.varSelected(item)
        self.readButtonClicked()
    
    def updateVarList(self, idx):
        """ Updates the listed variables based on the selected node """
        self.ui.variableList.clear()
        try:
            self.ui.variableList.addItems([var[1].signal_name for var in utils.signals[utils.b_str][self.ui.nodeSelector.currentText()][f"daq_response_{self.ui.nodeSelector.currentText().upper()}"].items()])
        except KeyError:
            pass # empty
    
    def readButtonClicked(self):
        """ Requests a variable read operation """
        self.ui.currValDisp.setText("Reading...")
        self.daq_protocol.readVar(self.curr_var)
    
    def writeButtonClicked(self):
        """ Requests a variable write operation """
        try:
            new_value = float(self.ui.newValDisp.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Write Error", "Write failed. Please enter an number")
            return
        if not self.curr_var.valueSendable(new_value):
            self.ui.newValDisp.setText(str(new_value) + f" <- Invalid for send dtype: {str(self.curr_var.send_dtype)}, scale: {self.curr_var.scale}, offset: {self.curr_var.offset})")
            return
        
        # Convey that the current value displayed may be old
        prev_text = self.ui.currValDisp.text()
        if len(prev_text) > 0 and "(previous)" not in prev_text:
            self.ui.currValDisp.setText(prev_text + " (previous)")

        self.changes_unsaved = True
        self.handleSaveProgress(self.save_in_prog)
        self.daq_protocol.writeVar(self.curr_var, new_value)

    def saveButtonClicked(self):
        """ Requests a variable save operation """
        self.changes_unsaved = False
        self.daq_protocol.saveFile(self.curr_var)
    
    def loadButtonClicked(self):
        """ Requests a variable load operation """
        # Convey that the current value displayed may be old
        prev_text = self.ui.currValDisp.text()
        if len(prev_text) > 0 and "(previous)" not in prev_text:
            self.ui.currValDisp.setText(prev_text + " (previous)")

        self.daq_protocol.loadFile(self.curr_var)
    
    def startPubButtonClicked(self):
        """ Requests a variable publish operation """
        try:
            period = int(self.ui.pubPeriodDisp.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Pub Error", "Pub failed. Please enter an integer")
            return
        if period < 0 or period > 255 * 15:
            self.ui.newValDisp.setText(str(period) + f" <- out of range (max: {255 * 15} ms)")
            return
        self.daq_protocol.pubVar(self.curr_var, period)
    
    def stopPubButtonClicked(self):
        """ Requests a stop publish operation """
        self.ui.pubPeriodDisp.setText("0")
        self.daq_protocol.pubVarStop(self.curr_var)

    def handleReceive(self):
        """ Updates the current value displayed when the subscribed variable is updated """
        self.ui.currValDisp.setText(str(self.curr_var.curr_val))
    
    def handleSaveProgress(self, in_progress):
        """ Callback for displaying the status of a save operation """
        self.save_in_prog = in_progress
        self.ui.loadButton.setDisabled(self.save_in_prog or self.curr_var.file_lbl == None or self.curr_var.read_only)
        status = "busy" if in_progress else "idle"
        if self.changes_unsaved:
            status += "\nCaution: unsaved changes."
        self.ui.saveStatLbl.setText("Save status: " + status)