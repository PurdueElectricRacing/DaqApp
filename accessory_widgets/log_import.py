from communication.can_bus import CanBus
import utils
from PyQt5 import QtWidgets
from ui.logImport import Ui_logImport
import can

class LogImporter(QtWidgets.QDialog):
    """ Log import tool for log files """

    def __init__(self, bus: CanBus, parent=None):
        super(LogImporter, self).__init__(parent=parent)
        self.ui = Ui_logImport()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.fileButton.clicked.connect(self.selectFile)
        self.ui.importButton.clicked.connect(self.importFile)


        self.bus = bus
        self.file_locations = []

    def selectFile(self):
        self.file_locations, _ = QtWidgets.QFileDialog.getOpenFileNames(self, filter="*.log")
        self.ui.fileSelectLabel.setText(', '.join([loc.split('/')[-1] for loc in self.file_locations]))

    def importFile(self, path):
        """ reads a file, parsing the frames as it goes """

        # TODO: warn that this will clear current data
        # read each line
        # parse line into can.Message
        # decode and update corresponding signal object

        started_paused = self.bus.is_paused
        if started_paused: self.bus.pause(False)

        # clear current data
        if not self.ui.joinCheck.isChecked():
            utils.clearDictItems(utils.signals)
            self.bus.start_time_bus = -1

        for path in self.file_locations:
            with open(path, 'r') as log:
                for line in log.readlines():
                    cols = line.split(" ")
                    time = float(cols[0][1:-2])
                    id, data = cols[2].split('#')
                    dlc = int(len(data)/2)
                    msg = can.Message(timestamp=time,
                                    is_extended_id=True,
                                    dlc=dlc,
                                    data=int(data, base=16).to_bytes(dlc, 'big'),
                                    arbitration_id=int(id, base=16))
                    self.bus.onMessageReceived(msg)
        
        if started_paused: self.bus.pause(True)

        self.accept()

    @staticmethod
    def importLog(bus:CanBus, parent=None):
        """ Open the log import dialog """
        importer = LogImporter(bus, parent=parent)
        importer.exec_()

