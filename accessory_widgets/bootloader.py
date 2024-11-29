import os
from PyQt5 import QtWidgets, QtCore, QtGui
import time
from ui.bootloader import Ui_Bootloader
import utils
from intelhex import IntelHex

from tools.canbus import CANBus
from tools.flash import CANBootloader

class Bootloader(QtWidgets.QWidget):
    """ Widget that handles bootloader firmware downloads """

    blacklist = ["bootloader", "BITSTREAM"]
    bl_msg_ending = "_bl_resp"

    def __init__(self, bus, firmware_path, parent=None):
        super(Bootloader, self).__init__(parent)
        self.ui = Ui_Bootloader()
        self.ui.setupUi(self)

        #self.bus = bus
        self.ih = None # Intel Hex

        # Signal connections
        self.ui.nodeSelector.currentIndexChanged.connect(self.updateNode)
        self.ui.fileBtn.clicked.connect(self.selectFile)
        self.ui.rstBtn.clicked.connect(self.requestReset)
        self.ui.flashBtn.clicked.connect(self.requestFlash)

        self.ui.indicators = []
        self.firmware_path = firmware_path
        self.hex_loc = ""
        self.bl = None
        self.calcNodes()
        self._logInfo(f"{len(self.bl_nodes)} bootloader nodes loaded")

        self.ui.autoReloadCheckbox.stateChanged.connect(self.toggleAutoReload)
        self.autoReload = True

    def toggleAutoReload(self, state):
        self.autoReload = bool(state)

    def calcNodes(self):
        # Determine node names from bus
        self.nodes = []
        for node in utils.signals[utils.b_str]:
            if (node not in self.blacklist):
                self.nodes.append(node)
                self.addStatusIndicator(node)

        # Determine which nodes are bootloader enabled
        self.bl_nodes = []
        self.ui.nodeSelector.clear()
        if 'bootloader' not in utils.signals[utils.b_str]: # Not a bootloader enabled bus
            return
        for msg in utils.signals[utils.b_str]['bootloader']:
            self.bl_nodes.append(msg[:-len(self.bl_msg_ending)])
        self.ui.nodeSelector.addItems(self.bl_nodes)

    def updateNode(self, idx):
        """ Updates the selected bootloader node """
        self.hex_loc = ""
        self.selected_node = self.bl_nodes[idx].lower()
        #self.bl = BootloaderCommand(self.selected_node, self.bus.db)
        # Try to find HEX file associated with node
        node_path = self.firmware_path + f"/output/{self.selected_node}/BL_{self.selected_node}.hex"
        self.verifyHex(node_path)

    def selectFile(self):
        selected, _ = QtWidgets.QFileDialog.getOpenFileName(self, filter="*.hex", directory=self.firmware_path)
        self.verifyHex(selected)

    def verifyHex(self, path):
        if (path != "" and os.path.exists(path)):
            self.hex_loc = path
            self.ui.currFileLbl.setText(self.hex_loc)

            self.ih = IntelHex()
            self.ih.fromfile(path, format="hex")
            self.segments = self.ih.segments()

            for seg in self.segments:
                self._logInfo(f"Segment: 0x{seg[0]:02X} : 0x{seg[1]:02X}")
            if (self.segments[0][0] < 0x8002000):
                self.ui.currFileLbl.setText("Please select file")
                self._logInfo(f"Invalid start address, ensure the hex is of type BL_ and starts at >= 0x8002000")
                self.hex_loc = ""
                return
        else:
            self.ui.currFileLbl.setText("Please select file")
            self._logInfo(f"Unable to find hex at {path}")

    def requestReset(self):
        self._logInfo(f"Reset {self.selected_node}")
        canbus = CANBus()
        canbus.connect()
        cb = CANBootloader(canbus)
        cb.request_reset(self.selected_node)
        canbus.disconnect()

    def requestFlash(self):
        self._logInfo(f"Flashing {self.selected_node}")
        canbus = CANBus()
        canbus.connect()
        cb = CANBootloader(canbus)
        start = time.time()
        cb.firmware_flash(self.selected_node, self.hex_loc)
        end = time.time()
        canbus.disconnect()
        delta = end - start
        self.ui.progressBar.setValue(100)
        self._logInfo(f"Flashed {self.selected_node}. Time: {delta:.3f}s")
        #self.ui.flashBtn.setDisabled(True)
        #self.ui.rstBtn.setDisabled(True)
        #self.ui.nodeSelector.setDisabled(True)

    def addStatusIndicator(self, name):
        indic = QtWidgets.QRadioButton(self)
        font = QtGui.QFont()
        font.setPointSize(10)
        indic.setFont(font)
        indic.setCheckable(False)
        indic.setChecked(False)
        indic.setText(name)
        self.ui.indicators.append(indic)
        self.ui.verticalLayout_3.insertWidget(len(self.ui.indicators), indic)

    def _logInfo(self, msg):
        self.ui.informationTxt.appendPlainText(msg)
