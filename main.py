from PyQt5 import QtWidgets, QtCore, QtGui
from accessory_widgets.bootloader.bootloader import Bootloader
from accessory_widgets.frame_viewer import FrameViewer
from accessory_widgets.car_viewer import CarViewer
from accessory_widgets.cell_viewer import CellViewer
from accessory_widgets.charge_viewer import ChargeViewer
from accessory_widgets.faultViewer import FaultViewer
from accessory_widgets.log_export import LogExporter
from accessory_widgets.log_import import LogImporter
from accessory_widgets.motor_viewer import MotorViewer
from accessory_widgets.preferences_editor import PreferencesEditor
from accessory_widgets.variable_editor import VariableEditor
from accessory_widgets.file_viewer import FileViewer
from accessory_widgets.sensor_viewer import SensorViewer
from accessory_widgets.system_monitor import SystemMonitor
from display_widgets.plot_widget import PlotWidget
from display_widgets import plot_widget
from communication.can_bus_selector import CanBusSelector
from communication.can_bus import CanBus
from communication.daq_protocol import DaqProtocol
from communication.time_sync_status import TimeSyncStatus
from display_widgets.lcd_widget import LcdDisplay
from display_widgets.widget_deleter import WidgetDeleter
from ui.mainWindow import Ui_MainWindow
import datetime as dt
import webbrowser
import qdarkstyle
import threading
import utils
import json
import time
import sys
import can
import os

# File location changes when converted to exe
if getattr(sys, 'frozen', False):
    CurrentPath = sys._MEIPASS
else:
    CurrentPath = os.path.dirname(__file__)

CONFIG_FILE_PATH = os.path.join(os.getcwd(), "dashboard.json")

class Main(QtWidgets.QMainWindow):

    timeEventTimedOut = QtCore.pyqtSignal()

    def __init__(self, config):
        super(Main, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        print(sys.platform)
        # Load Configurations (dictionaries)
        firmware_base = config['firmware_path']
        self.daq_config = utils.load_json_config(os.path.join(firmware_base, 'common/daq/daq_config.json'), os.path.join(firmware_base, 'common/daq/daq_schema.json'))
        self.can_config = utils.load_json_config(os.path.join(firmware_base, 'common/daq/can_config.json'), os.path.join(firmware_base, 'common/daq/can_schema.json'))
        self.fault_config = utils.load_json_config(os.path.join(firmware_base, 'common/faults/fault_config.json'), os.path.join(firmware_base, 'common/faults/fault_schema.json'))
        self.fault_config = DaqProtocol.create_ids(self, self.fault_config)

        # Can Bus Initialization
        # Default to the VCAN DBC, but this will be configurable.
        self.can_bus = CanBus(os.path.join(firmware_base, 'common/daq/per_dbc_VCAN.dbc'), config['default_ip'], self.can_config, firmware_base)
        self.can_bus.connect_sig.connect(self.updateConnectionStatus)
        self.can_bus.write_sig.connect(self.updateWriteConnectionStatus)
        self.can_bus.bus_load_sig.connect(self.updateBusLoad)
        self.can_bus.uds_msg_sig.connect(self.handleTimeStampUpdate)
        self.daq_protocol = DaqProtocol(self.can_bus, self.daq_config)
        self.old_time = None

        self.timeEventTimedOut.connect(self.timeStampUpdateTimedOut)

        # Status Bar
        self.ui.comlbl = QtWidgets.QLabel()
        self.ui.loadlbl = QtWidgets.QLabel()
        self.ui.loadlbl.setStyleSheet("font:16px;")
        self.ui.eventTextEdit = QtWidgets.QLineEdit(text='Event')
        self.ui.eventButton = QtWidgets.QPushButton('Log Event')
        self.ui.loginButton = QtWidgets.QPushButton('Write to Car')
        self.ui.logoutButton = QtWidgets.QPushButton('Stop Writing to Car')
        self.ui.logEnableBtn = QtWidgets.QPushButton('Start Logging')
        self.ui.logDisableBtn = QtWidgets.QPushButton('Stop Logging')
        self.ui.syncTimeBtn = QtWidgets.QPushButton('Sync Time with Car')
        self.ui.eventButton.setStyleSheet("border-color: black; border-style: outset; border-width: 2px;")
        self.ui.writelbl = QtWidgets.QLabel()
        self.ui.statusbar.addWidget(self.ui.comlbl)
        self.ui.statusbar.addWidget(self.ui.loadlbl)
        self.ui.statusbar.addWidget(self.ui.eventTextEdit)
        self.ui.statusbar.addWidget(self.ui.eventButton)
        self.ui.statusbar.addWidget(self.ui.loginButton)
        self.ui.statusbar.addWidget(self.ui.logoutButton)
        self.ui.statusbar.addWidget(self.ui.writelbl)
        self.ui.statusbar.addWidget(self.ui.logEnableBtn)
        self.ui.statusbar.addWidget(self.ui.logDisableBtn)
        self.ui.statusbar.addWidget(self.ui.syncTimeBtn)
        self.ui.eventButton.clicked.connect(self.logEvent)
        self.ui.loginButton.clicked.connect(self.loginEvent)
        self.ui.logoutButton.clicked.connect(self.logoutEvent)
        self.ui.logEnableBtn.clicked.connect(self.logEvent)
        self.ui.logDisableBtn.clicked.connect(self.logDisableEvent)
        self.ui.syncTimeBtn.clicked.connect(self.syncTimeEvent)

        # Menu Bar Tools
        self.ui.play_icon = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay'))
        self.ui.pause_icon = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPause'))
        self.ui.clear_icon = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_DialogResetButton'))
        self.ui.reconnect_icon = self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_BrowserReload'))
        self.ui.actionPlayPause = QtWidgets.QAction(self.ui.play_icon, "play_pause", self.ui.menubar)
        self.ui.actionClear = QtWidgets.QAction(self.ui.clear_icon, "clear", self.ui.menubar)
        self.ui.actionReconnect = QtWidgets.QAction(self.ui.reconnect_icon, "reconnect", self.ui.menubar)
        self.recording = False
        self.ui.menubar.addAction(self.ui.actionPlayPause)
        self.ui.menubar.addAction(self.ui.actionClear)
        self.ui.menubar.addAction(self.ui.actionReconnect)

        # Accessory Layout
        self.ui.accessoryLayout = QtWidgets.QVBoxLayout()
        self.ui.accessoryLayoutWidget = QtWidgets.QWidget()
        self.ui.accessoryLayoutWidget.setLayout(self.ui.accessoryLayout)

        self.ui.varEdit = VariableEditor(self.daq_protocol)
        self.ui.fileViewer = FileViewer()
        self.ui.frameViewer = FrameViewer(self.can_bus, self.ui.centralwidget)
        self.ui.accessoryLayout.addWidget(self.ui.frameViewer)
        self.ui.cellViewer  = CellViewer(self.can_bus)
        self.ui.logExporter = LogExporter(self.can_bus)
        self.ui.bootloader  = Bootloader(self.can_bus, config['firmware_path'])
        self.ui.chargeViewer  = ChargeViewer(self.can_bus)
        self.ui.faultViewer = FaultViewer(self.can_bus, self.fault_config, self.daq_protocol)
        self.ui.sensorViewer = SensorViewer(self.can_bus)
        self.ui.systemMonitor = SystemMonitor(self.can_bus)
        self.ui.motorViewer = MotorViewer(self.can_bus)
        self.ui.carViewer = CarViewer(self.can_bus)

        # Dashboard Layout
        self.ui.dashboardLayout = QtWidgets.QGridLayout()
        self.ui.dashboardLayoutWidget = QtWidgets.QWidget()
        self.ui.dashboardLayoutWidget.setLayout(self.ui.dashboardLayout)

        # Horizontally Split Accessory and Dashboard Layouts
        self.ui.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.ui.splitter.addWidget(self.ui.accessoryLayoutWidget)
        self.ui.splitter.addWidget(self.ui.dashboardLayoutWidget)
        self.ui.horizontalLayout.addWidget(self.ui.splitter)

        # Dashboard grid tracking
        self.ui.display_widgets = []
        self.curr_loc = [0, 0]
        self.max_rows = 1
        self.max_cols = 1

        # Menu Action Connections
        self.ui.actionImport_log.triggered.connect(lambda : LogImporter.importLog(self.can_bus, self))
        self.ui.actionVariable_Editor.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.varEdit))
        self.ui.actionFile_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.fileViewer))
        self.ui.actionFrame_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.frameViewer))
        self.ui.actionCell_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.cellViewer))
        self.ui.actionLog_Exporter.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.logExporter))
        self.ui.actionBootloader.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.bootloader))
        self.ui.actionCharge_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.chargeViewer))
        self.ui.actionSensor_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.sensorViewer))
        self.ui.actionSystem_Monitor.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.systemMonitor))
        self.ui.actionFault_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.faultViewer))
        self.ui.actionMotor_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.motorViewer))
        self.ui.actionCar_Viewer.triggered.connect(lambda _visible: self.viewWidget(_visible, self.ui.carViewer))
        self.ui.actionLCD.triggered.connect(self.newLCD)
        self.ui.actionPlot.triggered.connect(self.newPlot)
        self.ui.actionRemoveWidget.triggered.connect(self.removeDisplayWidget)
        self.ui.actionLoad_View.triggered.connect(self.loadView)
        self.ui.actionSave_View.triggered.connect(self.saveView)
        self.ui.actionPreferences.triggered.connect(lambda : PreferencesEditor.editPreferences(self.ui.varEdit, parent=self))
        self.ui.actionSelect_CAN_Bus.triggered.connect(lambda: CanBusSelector(self, self.can_config))
        self.ui.actionPlayPause.triggered.connect(self.playPause)
        self.ui.actionClear.triggered.connect(self.clearData)
        self.ui.actionReconnect.triggered.connect(self.can_bus.reconnect)
        self.ui.actionAbout.triggered.connect(lambda: webbrowser.open(
                            'https://wiki.itap.purdue.edu/display/PER22/Data+Acquisition'))

        self.updateWriteConnectionStatus(0)
        self.can_bus.connect()
        self.can_bus.start()
        # self.can_bus.reconnect()
        self.show()

    def updateConnectionStatus(self, connected: bool):
        """ Updates the connection status label when connect status changes """
        if connected:
            self.ui.comlbl.setStyleSheet("color: green; font: 18px bold;")
            self.ui.comlbl.setText("Connected")
        else:
            self.ui.comlbl.setStyleSheet("color: red; font: 18px bold;")
            self.ui.comlbl.setText("Disconnected")
        self.ui.varEdit.setDisabled(not connected)
        self.ui.frameViewer.setDisabled(not connected)

    def updateWriteConnectionStatus(self, tcpconnected: int):
        """ Updates the connection status label when connect status changes """
        if tcpconnected == 2:
            self.ui.writelbl.setStyleSheet("color: green; font: 18px bold;")
            self.ui.writelbl.setText("Connected")
        elif tcpconnected == 1:
            self.ui.writelbl.setStyleSheet("color: yellow; font: 18px bold;")
            self.ui.writelbl.setText("Connecting...")
        elif tcpconnected == 0:
            self.ui.writelbl.setStyleSheet("color: red; font: 18px bold;")
            self.ui.writelbl.setText("Disconnected")



    def updateBusLoad(self, load: float):
        """ Updates the bus load label """
        self.ui.loadlbl.setText(f"Bus Load: {load:.2f}%")

    def viewWidget(self, is_visible: bool, widget):
        """ Hides or shows a widget """
        if is_visible:
            self.ui.accessoryLayout.addWidget(widget)
            widget.show()
        else:
            self.ui.accessoryLayout.removeWidget(widget)
            widget.hide()

    def newLCD(self):
        """ Adds a new LCD dashboard widget """
        self.ui.display_widgets.append(LcdDisplay(utils.signals, self))
        self.addDashWidget(self.ui.display_widgets[-1])

    def newPlot(self):
        """ Adds a new Plot dashboard widget """
        self.ui.display_widgets.append(PlotWidget(utils.signals, self))
        self.addDashWidget(self.ui.display_widgets[-1])

    def addDashWidget(self, widget):
        """ Adds a widget to the dashboard and calcualtes the next grid location """
        self.ui.dashboardLayout.addWidget(widget, *self.curr_loc)

        # add new column, then new row until a square is reached
        if self.curr_loc[0] == self.curr_loc[1] == (self.max_rows - 1) == (self.max_cols - 1):
            self.max_cols += 1
            self.curr_loc[0] = 0
        if self.curr_loc[1] == (self.max_cols - 1):
            self.curr_loc[0] += 1

            if self.curr_loc[0] > (self.max_rows - 1):
                self.curr_loc[1] = 0
                self.max_rows += 1
        else:
            self.curr_loc[1] += 1

    def removeDisplayWidget(self):
        """ removes a display widget and resets the grid locations """
        for w in self.ui.display_widgets:
            self.ui.dashboardLayout.removeWidget(w)
        widgets_to_delete = WidgetDeleter.getWidgets(self.ui.display_widgets)
        for w in widgets_to_delete:
            w.destroy()
            self.ui.display_widgets.remove(w)
        # Reset axis link (in case the plot that all the
        #                  axes were linked to was deleted)
        plot_widget.view_box_link = None
        for w in self.ui.display_widgets:
            w.signalsChanged()
        # redo grid layout
        self.curr_loc = [0, 0]
        self.max_rows = 1
        self.max_cols = 1
        for w in self.ui.display_widgets:
            self.addDashWidget(w)

    def loadView(self):
        """ Loads a widget display from a file, clears the current view"""

        # Load file
        file_loc, _ = QtWidgets.QFileDialog.getOpenFileName(self, filter="*.daqview")

        # Check no file
        if not file_loc: return
        config = None
        with open(file_loc, 'r') as f:
            config = f.read()
        if not config:
            utils.log_error(f"Invalid view file: {file_loc}")
            return

        # Parse
        new_display_widgets = []
        widgets = config.split(';')
        for w in widgets[:-1]:
            name, sigs = w.split(':')
            sig_def = json.loads(sigs)
            chosen_sigs = []
            for sig in sig_def[0]:
                if sig[0] != utils.b_str:
                    utils.log_warning(f"Adding signal on bus {sig[0]}, but currently on bus {utils.b_str}")
                try:
                    chosen_sigs.append(utils.signals[sig[0]][sig[1]][sig[2]][sig[3]])
                    # set color
                    chosen_sigs[-1].color = QtGui.QColor(*sig[4])
                except KeyError:
                    # utils.log_error(f"Unrecognized signal key for {sig[3]}")
                    return
            if 'PlotWidget' in name:
                new_display_widgets.append(PlotWidget(utils.signals, parent=self, selected_signals=chosen_sigs))
            elif 'LcdDisplay' in name:
                new_display_widgets.append(LcdDisplay(utils.signals, parent=self, selected_signals=chosen_sigs))
            else:
                utils.log_error(f"Invalid widget type {name}")
                return

        # Clear current view
        for w in self.ui.display_widgets:
            self.ui.dashboardLayout.removeWidget(w)
            w.destroy()
            self.ui.display_widgets.remove(w)
        # Reset axis link (in case the plot that all the
        #                  axes were linked to was deleted)
        plot_widget.view_box_link = None
        self.curr_loc = [0, 0]
        self.max_rows = 1
        self.max_cols = 1

        # add
        for w in new_display_widgets:
            self.ui.display_widgets.append(w)
            self.addDashWidget(self.ui.display_widgets[-1])

    """
    PlotWidget:[(bus, node, message, sig, (r,g,b,a)),
                (bus, node, message, sig, (r,g,b,a))];
    PlotWidget:[(bus, node, message, sig, (r,g,b,a)),];
    """
    def saveView(self):
        """ Saves the current widget display"""
        output_data = ""
        for w in self.ui.display_widgets:
            w_str = ""
            if type(w) is PlotWidget:
                w_str = "PlotWidget:["
            elif type(w) is LcdDisplay:
                w_str = "LcdDisplay:["
            else:
                pass
            sigs = [[sig.bus_name,sig.node_name, sig.message_name, sig.signal_name, list(sig.color.getRgb())] for sig in w.current_signals]
            w_str += str(sigs).replace("'","\"") + "];\n"
            output_data += w_str

        file_location, _ = QtWidgets.QFileDialog.getSaveFileName(self, filter="*.daqview")
        with open(file_location, 'w') as f:
            f.write(output_data)

    def playPause(self):
        """ Start recording signal values """
        self.recording = not self.recording
        if self.recording:
            self.ui.actionPlayPause.setIcon(self.ui.pause_icon)
        else:
            self.ui.actionPlayPause.setIcon(self.ui.play_icon)
        self.can_bus.pause(not self.recording)

    def clearData(self):
        """ Clears recorded signal values """
        utils.clearDictItems(utils.signals)
        utils.clearEvents()
        self.can_bus.start_time_bus = -1

    def logEvent(self):
        """ Logs and event, recording the timestamp """
        t = time.time() - self.can_bus.start_time_cmp
        utils.logEvent(t, self.ui.eventTextEdit.text())

    def loginEvent(self):
        """ Attempts to connect to TCP server """
        self.can_bus.connect_tcp()

    def logoutEvent(self):
        """Attempts to disconnect from TCP server"""
        self.can_bus.disconnect_tcp()

    def logEvent(self):
        """Attempts to start PI Logger"""
        self.can_bus.sendLogCmd(True)

    def logDisableEvent(self):
        """Attempts to stop the PI logger"""
        self.can_bus.sendLogCmd(False)

    def syncTimeEvent(self):
        """Attempts to sync RTC Time With DAQ PCB"""
        current_time = dt.datetime.now()
        utils.log_warning(f"Attempting to sync DAQ time to {current_time}. Year: {current_time.year}, Month: {current_time.month}, Weekday: {current_time.weekday() + 1}, Day: {current_time.day}, Hour: {current_time.hour}, Minute: {current_time.minute}, Second: {current_time.second}")
        # 64 bit int following scheme in daq_uds.c to form msg payload
        # Byte 0: Command, Byte 1: Seconds Byte 2: Minutes Byte 3: Hours Byte 4: Year Byte 5: Month Byte 6: Weekday Byte 7: Day
        # I think the year will need to be encoded differently
        # data = bytes([0x60, current_time.second, current_time.minute, current_time.hour, (current_time.year - 2000), current_time.month, (current_time.weekday() + 1), current_time.day])
        year_tens = (int)((current_time.year - 2000) / 10)
        year_units = (current_time.year) % 10
        year = ((year_tens << 4) | year_units)
        month_tens = (int)((current_time.month) / 10)
        month_units = (current_time.month) % 10
        month = ((month_tens << 4) | month_units)
        day_tens = (int)((current_time.day) / 10)
        day_units = (current_time.day) % 10
        day = ((day_tens << 4) | day_units)
        hours_tens = (int)((current_time.hour) / 10)
        hours_units = (current_time.hour) % 10
        hours = ((hours_tens << 4) | hours_units)
        minutes_tens = (int)((current_time.minute) / 10)
        minutes_units = (current_time.minute) % 10
        minutes = ((minutes_tens << 4) | minutes_units)
        seconds_tens = (int)((current_time.second) / 10)
        seconds_units = (current_time.second) % 10
        seconds = ((seconds_tens << 4) | seconds_units)

        data = bytes([0x60, day, (current_time.weekday() + 1),  month, year, hours, minutes, seconds])
        msg_from_dbc = self.can_bus.db.get_message_by_name("uds_command_daq")
        self.can_bus.sendMsg(can.Message(arbitration_id=msg_from_dbc.frame_id,
                                         is_extended_id=True,
                                         data=data))

        self.timeEventTimedOutTimer = threading.Timer(7, self.timeOutPrepare)
        self.confirmUpdateTimer = threading.Timer(5, self.confirmUpdatedTime)

        self.timeEventTimedOutTimer.start()
        self.confirmUpdateTimer.start()

    def confirmUpdatedTime(self):
        utils.log_warning("Retrieving Updated time:")
        msg_from_dbc = self.can_bus.db.get_message_by_name("uds_command_daq")
        self.can_bus.sendMsg(can.Message(arbitration_id=msg_from_dbc.frame_id,
                                         is_extended_id=True,
                                         data=bytes([0x61, 0, 0, 0, 0, 0, 0, 0])))

    def handleTimeStampUpdate(self, msg: can.Message):
        utils.log_success("Response Recieved from UDS!")



        # dbc_msg = self.can_bus.db.get_message_by_frame_id(msg.arbitration_id)
        data = int.from_bytes(msg.data, "little")
        day = (data >> 0) & 0xff
        weekday = (data >> 8) & 0xff
        month = (data >> 16) & 0xff
        year = (data >> 24) & 0xff

        hours = (data >> 32) & 0xff
        minutes = (data >> 40) & 0xff
        seconds = (data >> 48) & 0xff

        ret_code = (data >> 56) & 0xff

        utils.log_success(f"Data: Ret code: {ret_code}, Year: {year}, Month: {month}, Weekday: {weekday}, Day: {day}, Hour: {hours}, Minute: {minutes}, Second: {seconds}")

        if (ret_code == 0):
            self.old_time = f"{month}/{day}/{year}, {hours}:{minutes}:{seconds}"
        else:
          self.timeEventTimedOutTimer.cancel()
          TimeSyncStatus(old_time=self.old_time, new_time=f"{month}/{day}/{year}, {hours}:{minutes}:{seconds}", ret_code=ret_code)
          self.old_time = None


    def timeOutPrepare(self):
        self.timeEventTimedOut.emit()

    def timeStampUpdateTimedOut(self):
        utils.log_error("Timed out loser")

        if (self.old_time is None):
          TimeSyncStatus(None, None, ret_code=5)
        else:
          self.old_time = None
          TimeSyncStatus(None, None, ret_code=4)



    def closeEvent(self, event):
        """ Called on exit of main window """
        if self.can_bus.connected:
            self.can_bus.connected = False
            while(not self.can_bus.isFinished()):
                # wait for bus receive to finish
                pass
        self.can_bus.disconnect_bus()
        event.accept()

if __name__ == "__main__":
    utils.initGlobals()

    config = json.load(open(CONFIG_FILE_PATH))
    app = QtWidgets.QApplication(sys.argv)

    # Style Configuration
    if config['dark_mode']:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setWindowIcon(QtGui.QIcon(os.path.join(CurrentPath, "ui/logo.png")))

    utils.debug_mode = config['debug']
    utils.dark_mode = config['dark_mode']

    window = Main(config)
    app.exec_()
