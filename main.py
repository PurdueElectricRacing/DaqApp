from PyQt5 import QtWidgets, QtCore, QtGui
from accessory_widgets.bootloader.bootloader import Bootloader
from accessory_widgets.frame_viewer import FrameViewer
from accessory_widgets.cell_viewer import CellViewer
from accessory_widgets.charge_viewer import ChargeViewer
from accessory_widgets.faultViewer import FaultViewer
from accessory_widgets.log_export import LogExporter
from accessory_widgets.log_import import LogImporter
from accessory_widgets.preferences_editor import PreferencesEditor
from accessory_widgets.variable_editor import VariableEditor
from accessory_widgets.file_viewer import FileViewer
from accessory_widgets.sensor_viewer import SensorViewer
from accessory_widgets.system_monitor import SystemMonitor
from display_widgets.plot_widget import PlotWidget
from display_widgets import plot_widget
from communication.can_bus import CanBus
from communication.daq_protocol import DaqProtocol
from display_widgets.lcd_widget import LcdDisplay
from display_widgets.widget_deleter import WidgetDeleter
from ui.mainWindow import Ui_MainWindow
import webbrowser
import qdarkstyle
import utils
import json
import time
import sys
import os

# File location changes when converted to exe
if getattr(sys, 'frozen', False):
    CurrentPath = sys._MEIPASS
else:
    CurrentPath = os.path.dirname(__file__)

CONFIG_FILE_PATH = os.path.join(os.getcwd(), "dashboard.json")

class Main(QtWidgets.QMainWindow):

    def __init__(self, config):
        super(Main, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        print(sys.platform)
        # Load Configurations (dictionaries)
        self.daq_config = utils.load_json_config(config['daq_config_path'], config['daq_schema_path'])
        self.can_config = utils.load_json_config(config['can_config_path'], config['can_schema_path'])
        self.fault_config = utils.load_json_config(config['fault_config_path'], config['fault_schema_path'])
        self.fault_config = DaqProtocol.create_ids(self, self.fault_config)

        # Can Bus Initialization
        self.can_bus = CanBus(config['dbc_path'], config['default_ip'], self.can_config)
        self.can_bus.connect_sig.connect(self.updateConnectionStatus)
        self.can_bus.bus_load_sig.connect(self.updateBusLoad)
        self.daq_protocol = DaqProtocol(self.can_bus, self.daq_config)

        # Status Bar
        self.ui.comlbl = QtWidgets.QLabel()
        self.ui.loadlbl = QtWidgets.QLabel()
        self.ui.loadlbl.setStyleSheet("font:16px;")
        self.ui.eventTextEdit = QtWidgets.QLineEdit(text='Event')
        self.ui.eventButton = QtWidgets.QPushButton('Log Event')
        self.ui.loginButton = QtWidgets.QPushButton('Write to Car')
        self.ui.logoutButton = QtWidgets.QPushButton('Stop Writing to Car')
        self.ui.eventButton.setStyleSheet("border-color: black; border-style: outset; border-width: 2px;")
        self.ui.statusbar.addWidget(self.ui.comlbl)
        self.ui.statusbar.addWidget(self.ui.loadlbl)
        self.ui.statusbar.addWidget(self.ui.eventTextEdit)
        self.ui.statusbar.addWidget(self.ui.eventButton)
        self.ui.statusbar.addWidget(self.ui.loginButton)
        self.ui.statusbar.addWidget(self.ui.logoutButton)
        self.ui.writelbl = QtWidgets.QLabel()
        self.ui.eventButton.clicked.connect(self.logEvent)
        self.ui.loginButton.clicked.connect(self.loginEvent)
        self.ui.logoutButton.clicked.connect(self.logoutEvent)

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
        self.ui.actionLCD.triggered.connect(self.newLCD)
        self.ui.actionPlot.triggered.connect(self.newPlot)
        self.ui.actionRemoveWidget.triggered.connect(self.removeDisplayWidget)
        self.ui.actionLoad_View.triggered.connect(self.loadView)
        self.ui.actionSave_View.triggered.connect(self.saveView)
        self.ui.actionPreferences.triggered.connect(lambda : PreferencesEditor.editPreferences(self.ui.varEdit, parent=self))
        self.ui.actionPlayPause.triggered.connect(self.playPause)
        self.ui.actionClear.triggered.connect(self.clearData)
        self.ui.actionReconnect.triggered.connect(self.can_bus.reconnect)
        self.ui.actionAbout.triggered.connect(lambda: webbrowser.open(
                            'https://wiki.itap.purdue.edu/display/PER22/Data+Acquisition'))

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
                    utils.log_error(f"Unrecognized signal key for {sig[3]}")
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