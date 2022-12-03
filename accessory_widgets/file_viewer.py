from PyQt5 import QtWidgets, QtGui, QtCore
from communication.can_bus import BusSignal
from ui.fileViewer import Ui_fileViewer
import utils


class FileViewer(QtWidgets.QDialog):
    """ Used to view file content states """

    def __init__(self, parent=None):
        super(FileViewer, self).__init__(parent)
        self.ui = Ui_fileViewer()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.saveButton.clicked.connect(self.saveFile)
        self.ui.loadButton.clicked.connect(self.loadFile)
        self.ui.nodeSelector.currentIndexChanged.connect(self.updateFileCombo)
        self.ui.fileSelector.currentIndexChanged.connect(self.updateContentList)

        # Populate with items
        nodes_with_files = []
        for node_name in utils.signals[utils.b_str].keys():
            node_d = utils.signals[utils.b_str][node_name]
            if 'files' in node_d and len(node_d['files'].keys()) > 0:
                nodes_with_files.append(node_name)
        self.ui.nodeSelector.addItems(nodes_with_files)

        self.updateFileCombo()
        self.updateContentList()

        self.fps = 5
        self.var_timer = QtCore.QTimer()
        self.var_timer.timeout.connect(self.updateContentColors)

    def show(self) -> None:
        self.var_timer.start(int(1000.0/self.fps))
        return super().show()

    def hide(self) -> None:
        self.var_timer.stop()
        return super().hide()

    def updateFileCombo(self):
        """ Updates the file options """
        self.ui.fileSelector.clear()
        node_d = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()]
        # assumed node has files
        self.ui.fileSelector.addItems(node_d['files'].keys())

    def updateContentList(self):
        """ Updates the list of contents """
        try:
            self.ui.contentList.clear()
            node_d = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()]
            contents = node_d['files'][self.ui.fileSelector.currentText()]['contents']
            self.ui.contentList.addItems(contents)
            self.updateContentColors()
        except KeyError:
            pass

    def updateContentColors(self):
        if (not self.isVisible()): return
        try:
            node_d = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()]
            contents = node_d['files'][self.ui.fileSelector.currentText()]['contents']
            vars = node_d[f"daq_response_{self.ui.nodeSelector.currentText().upper()}"]
            for idx, var in enumerate(contents):
                item = self.ui.contentList.item(idx)
                if (vars[var].isDirty()): item.setBackground(QtGui.QColor(255,255, 127))
                else: item.setBackground(QtGui.QColor(255,255, 255))
        except KeyError:
            pass


    def loadFile(self):
        try:
            node_d = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()]
            contents = node_d['files'][self.ui.fileSelector.currentText()]['contents']
            vars = node_d[f"daq_response_{self.ui.nodeSelector.currentText().upper()}"]
            utils.daqProt.loadFile(vars[contents[0]])
            self.updateContentColors()
        except KeyError:
            pass

    def saveFile(self):
        try:
            node_d = utils.signals[utils.b_str][self.ui.nodeSelector.currentText()]
            contents = node_d['files'][self.ui.fileSelector.currentText()]['contents']
            vars = node_d[f"daq_response_{self.ui.nodeSelector.currentText().upper()}"]
            utils.daqProt.saveFile(vars[contents[0]])
            self.updateContentColors()
        except KeyError:
            pass
