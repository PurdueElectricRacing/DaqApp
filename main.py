from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import plot
from accessory_widgets.frame_viewer import FrameViewer
from accessory_widgets.preferences_editor import PreferencesEditor
from accessory_widgets.variable_editor import VariableEditor
from display_widgets.plot_widget import PlotWidget
from display_widgets import plot_widget
from communication.can_bus import CanBus
from communication.daq_protocol import DaqProtocol
from display_widgets.lcd_widget import LcdDisplay
from display_widgets.widget_deleter import WidgetDeleter
from ui.mainWindow import Ui_MainWindow
import qdarkstyle
import utils
import json
import sys
from display_widgets.gauge_widget import AnalogGaugeWidget


CONFIG_FILE_PATH = "./dashboard.json"

class Main(QtWidgets.QMainWindow):

    def __init__(self, config):
        super(Main, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Load Configurations (dictionaries)
        self.daq_config = utils.load_json_config(config['daq_config_path'], config['daq_schema_path'])
        self.can_config = utils.load_json_config(config['can_config_path'], config['can_schema_path'])

        # Can Bus Initialization
        self.can_bus = CanBus(config['dbc_path'], self.can_config)
        self.can_bus.connect_sig.connect(self.updateConnectionStatus)
        self.can_bus.bus_load_sig.connect(self.updateBusLoad)
        self.daq_protocol = DaqProtocol(self.can_bus, self.daq_config)

        # Status Bar
        self.ui.comlbl = QtWidgets.QLabel()
        self.ui.loadlbl = QtWidgets.QLabel()
        self.ui.loadlbl.setStyleSheet("font:16px;")
        self.ui.statusbar.addWidget(self.ui.comlbl)
        self.ui.statusbar.addWidget(self.ui.loadlbl)

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

        self.ui.varEdit = VariableEditor(self.daq_protocol, self.ui.centralwidget)
        self.ui.accessoryLayout.addWidget(self.ui.varEdit)
        self.ui.frameViewer = FrameViewer(self.can_bus)

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
        self.ui.actionVariable_Editor.triggered.connect(self.viewVariableEditor)
        self.ui.actionFrame_Viewer.triggered.connect(self.viewFrameViewer)
        self.ui.actionLCD.triggered.connect(self.newLCD)
        self.ui.actionPlot.triggered.connect(self.newPlot)
        self.ui.actionRemoveWidget.triggered.connect(self.removeDisplayWidget)
        self.ui.actionPreferences.triggered.connect(lambda : PreferencesEditor.editPreferences(self))
        self.ui.actionPlayPause.triggered.connect(self.playPause)
        self.ui.actionClear.triggered.connect(self.clearData)
        self.ui.actionReconnect.triggered.connect(self.can_bus.reconnect)

        self.can_bus.connect()
        self.can_bus.start()
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

    def viewVariableEditor(self, is_visible: bool):
        """ Hides or shows the variable editor  """
        if is_visible:
            self.ui.accessoryLayout.addWidget(self.ui.varEdit)
            self.ui.varEdit.show()
        else:
            self.ui.varEdit.hide()
            self.ui.accessoryLayout.removeWidget(self.ui.varEdit)
    
    def viewFrameViewer(self, is_visible: bool):
        """ Hides or shows the frame viewer """
        if is_visible:
            self.ui.accessoryLayout.addWidget(self.ui.frameViewer)
            self.ui.frameViewer.show()
        else:
            self.ui.accessoryLayout.removeWidget(self.ui.frameViewer)
            self.ui.frameViewer.hide()

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
        self.can_bus.start_time = -1

    def closeEvent(self, event):
        """ Called on exit of main window """
        self.can_bus.connected = False
        while(not self.can_bus.isFinished()):
            # wait for bus receive to finish
            pass
        event.accept()


if __name__ == "__main__":
    utils.initGlobals()

    config = json.load(open(CONFIG_FILE_PATH))
    app = QtWidgets.QApplication(sys.argv)

    # Style Configuration
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setWindowIcon(QtGui.QIcon('./ui/logo.png'))

    window = Main(config)
    app.exec_()