import math
import os
from PyQt5 import QtWidgets, QtCore, QtGui
import time
from accessory_widgets.bootloader.bootloader_commands import BootloaderCommand
from ui.bootloader import Ui_Bootloader
from communication.can_bus import CanBus
import can
import utils
from intelhex import IntelHex

from utils import log_warning

class Bootloader(QtWidgets.QWidget):
    """ Widget that handles bootloader firmware downloads """

    blacklist = ["bootloader", "BITSTREAM"]
    bl_msg_ending = "_bl_resp"

    reset_reasons = ["RESET_REASON_INVALID",
                     "RESET_REASON_BUTTON",
                     "RESET_REASON_DOWNLOAD_FW",
                     "RESET_REASON_APP_WATCHDOG",
                     "RESET_REASON_POR",
                     "RESET_REASON_BAD_FIRMWARE"]

    FLASH_STATE = {
        "WAIT_FOR_BL_MODE": 0,
        "WAIT_FOR_META_RESP": 1,
        "STREAMING_DATA": 2,
        "WAIT_FOR_STATUS": 3
    }

    def __init__(self, bus: CanBus, firmware_path, parent=None):
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
        #self.bus.bl_msg_sig.connect(self.handleNewBlMsg)
        """
        self.segments = None
        self.total_bytes = 0
        self.total_double_words = 0
        self.flash_active = False
        self.crc = 0xFFFFFFFF
        self.curr_addr = 0x00
        self.flash_state = self.FLASH_STATE['WAIT_FOR_BL_MODE']
        self.flash_timeout_timer = QtCore.QTimer()
        self.flash_timeout_timer.timeout.connect(self.flashTimeout)
        self.flash_start_time = 0
        """
        #self.flash_update_timer = QtCore.QTimer()
        #self.flash_update_timer.timeout.connect(self.flashTxUpdate)

        self.ui.indicators = []
        self.firmware_path = firmware_path
        self.hex_loc = ""
        self.bl = None
        self.calcNodes()
        self._logInfo(f"{len(self.bl_nodes)} bootloader nodes loaded")
        #self.flashReset(0)

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
                self.segments = None
                return
            self.total_bytes = self.segments[0][1] - self.segments[0][0]
            self.total_double_words = math.ceil(self.total_bytes / 8)
            print(self.total_double_words)

        else:
            self.ui.currFileLbl.setText("Please select file")
            self._logInfo(f"Unable to find hex at {path}")

    def requestReset(self):
        if (not self.bl): return
        msg = self.bl.firmware_rst_msg()
        self.bus.sendMsg(msg)
        self._logInfo(f"Reset {self.selected_node}")

    def requestFlash(self):
        if (not self.bl): return
        if self.autoReload:
            self.verifyHex(self.hex_loc)
        if (not self.segments):
            self._logInfo(f"Cannot flash {self.selected_node}, invalid hex")
            return
        self.flashReset(0)
        msg = self.bl.firmware_rst_msg()
        self.bus.sendMsg(msg)
        self.flash_active = True
        self.ui.flashBtn.setDisabled(True)
        self.ui.rstBtn.setDisabled(True)
        self.ui.nodeSelector.setDisabled(True)
        self.crc = 0xFFFFFFFF
        self._logInfo(f"Flashing {self.selected_node}")
        self.ui.progressBar.setValue(5)
        self.flash_timeout_timer.start(10000)
        self.flash_start_time = time.time()

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

    def handleNewBlMsg(self, msg: can.Message):
        if (not self.bl): return
        # Is message for selected node?
        if (msg.arbitration_id == self.bl.RX_MSG.frame_id):
            can_rx = self.bl.decode_msg(msg)
            if (can_rx['cmd'] == self.bl.RX_CMD['BLSTAT_BOOT']):
                self._logInfo(f"{list(self.bl.RX_CMD.keys())[can_rx['cmd']]}: {self.reset_reasons[can_rx['data']]}")
            # else:
            #     self._logInfo(f"{can_rx['cmd']}, {can_rx['data']}")
            if (self.flash_active):
                self.flashRxUpdate(can_rx['cmd'], can_rx['data'])
            # self._logInfo(f"state: {self.flash_state}")
        # TODO: change status based on reset reason / waiting for command

    def flashRxUpdate(self, cmd, data):
        """ Only called if message is from current node, and flash is active """
        if (cmd == self.bl.RX_CMD['BLSTAT_INVALID']):
            self._logInfo(f"BL Error: {self.bl.BL_ERROR[data]}")
            self.flashReset(0)
            return
        if (self.flash_state == self.FLASH_STATE['WAIT_FOR_BL_MODE']):
            if (cmd == self.bl.RX_CMD['BLSTAT_WAIT']):
                self.flash_timeout_timer.stop() # Entered bl mode, stop timeout timer
                self._logInfo("Sending firmware image metadata ...")
                msg = self.bl.firmware_size_msg(self.total_double_words * 2) # words
                self.bus.sendMsg(msg)
                self.flash_state = self.FLASH_STATE['WAIT_FOR_META_RESP']
                self.flash_timeout_timer.start(2000) # Time the rest of the flash process
        elif (self.flash_state == self.FLASH_STATE['WAIT_FOR_META_RESP']):
            if (cmd == self.bl.RX_CMD['BLSTAT_METDATA_RX']):
                self.flash_timeout_timer.stop()
                self._logInfo(f"Sending {self.hex_loc}...")
                self._logInfo(f"Total File Size: {self.total_bytes} Bytes")
                self.flash_timeout_timer.start(2000)
                self.curr_addr = self.segments[0][0]
                self.flash_state = self.FLASH_STATE['STREAMING_DATA']
                self.flash_update_timer.start(1)
        elif (self.flash_state == self.FLASH_STATE['STREAMING_DATA']):
            if (cmd == self.bl.RX_CMD['BLSTAT_PROGRESS']):
                self.flash_timeout_timer.stop()
                #self.flash_timeout_timer.start(2000) # reset timer
                self.flash_timeout_timer.start(10000) # reset timer
                #     self.curr_addr += 8
                #     if (self.curr_addr < self.segments[0][1]):
                #         # Not at end, send either 10 more or up to segments
                #         addr = self.curr_addr
                #         while addr - self.curr_addr < 1 * 8 and addr < self.segments[0][1]:
                #             self.sendSegmentDoubleWord(addr)
                #             addr += 8
                #         self.curr_addr = addr - 8 # the above while loop is guaranteed to run at least once
                #         self.ui.progressBar.setValue((90 * (self.curr_addr - self.segments[0][0])) / self.total_bytes + 5)
                #     else:
                #         self._logInfo("Sending CRC checksum")
                #         can_tx = self.bl.firmware_crc_msg(self.crc & 0xFFFFFFFF)
                #         self.bus.sendMsg(can_tx)
                #         self.flash_state = self.FLASH_STATE['WAIT_FOR_STATUS']
                # elif (data < self.curr_addr + 8):
                #     pass
                # else:
                #     self._logInfo(f"{cmd}|{data} != {self.curr_addr + 4}")
                #     self._logInfo("ERROR: Firmware download failed!!")
                #     self.flashReset(0)
        elif (self.flash_state == self.FLASH_STATE['WAIT_FOR_STATUS']):
            if (cmd != self.bl.RX_CMD['BLSTAT_PROGRESS']):
                self.flash_timeout_timer.stop()
                self.flash_update_timer.stop()
                if (cmd == self.bl.RX_CMD['BLSTAT_DONE']):
                    self._logInfo("Firmware download successful, CRC matched")
                    self.flashReset(100)
                else:
                    self._logInfo("ERROR: Firmware download failed!!")
                    self.flashReset(0)
                self._logInfo("Total time: %.2f seconds" % (time.time() - self.flash_start_time))

    def flashTxUpdate(self):
        if (self.flash_active and self.flash_state == self.FLASH_STATE['STREAMING_DATA']):
            if (self.curr_addr < self.segments[0][1]):
                self.sendSegmentDoubleWord(self.curr_addr)
                self.curr_addr += 8
                self.ui.progressBar.setValue(int((90 * (self.curr_addr - self.segments[0][0])) / self.total_bytes + 5))
            else:
                self._logInfo("Sending CRC checksum")
                can_tx = self.bl.firmware_crc_msg(self.crc & 0xFFFFFFFF)
                self.bus.sendMsg(can_tx)
                self.flash_state = self.FLASH_STATE['WAIT_FOR_STATUS']
        else:
            self.flash_update_timer.stop() # triggered unexpectedly

    def sendSegmentDoubleWord(self, addr):
        """ Only call if flash in progress """
        bin_arr = self.ih.tobinarray(start=addr, size=4)
        data1 = sum([x << ((i*8)) for i, x in enumerate(bin_arr)])
        self.crc = self.crc_update(data1, self.crc)

        if (addr + 4 >= self.segments[0][1]):
            data2 = 0
        else:
            bin_arr = self.ih.tobinarray(start=(addr + 4), size=4)
            data2 = sum([x << ((i*8)) for i, x in enumerate(bin_arr)])
        self.crc = self.crc_update(data2, self.crc)

        can_tx = self.bl.firmware_data_msg((data2 << 32) | data1)
        self.bus.sendMsg(can_tx)

    def flashTimeout(self):
        if (self.flash_active):
            if (self.flash_state <= self.FLASH_STATE['WAIT_FOR_BL_MODE']):
                self._logInfo("ERROR: Timed out waiting for node to enter bootloader state")
                self.flashReset(0)
            else:
                self._logInfo("ERROR: Timed out during flash")
                self.flashReset(0)
        else:
            self.flash_timeout_timer.stop() # triggered unexpectedly

    def flashReset(self, prog):
        self.flash_active = False
        self.flash_timeout_timer.stop()
        self.flash_update_timer.stop()
        self.flash_state = self.FLASH_STATE['WAIT_FOR_BL_MODE']
        self.ui.progressBar.setValue(prog)
        self.ui.flashBtn.setDisabled(False)
        self.ui.rstBtn.setDisabled(False)
        self.ui.nodeSelector.setDisabled(False)

    def _logInfo(self, msg):
        self.ui.informationTxt.appendPlainText(msg)

    # CRC-32b calculation
    CRC_POLY = 0x04C11DB7
    def crc_update(self, data, prev):
        crc = prev ^ data
        idx = 0
        while (idx < 32):
            if (crc & 0x80000000): crc = ((crc << 1) ^ self.CRC_POLY) & 0xFFFFFFFF
            else: crc = (crc << 1) & 0xFFFFFFFF
            idx += 1
        return crc