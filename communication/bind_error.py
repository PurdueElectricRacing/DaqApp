from PyQt5 import QtWidgets
from ui.bindError import Ui_Dialog
import sys

class BindError(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(BindError, self).__init__(parent=parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.dismiss.clicked.connect(self.closeWindow)

    def closeWindow(self):
        self.accept()

    @staticmethod
    def bindError(parent=None):
        """ Used when error connecting, returns new ip address """
        dialog = BindError(parent=parent)
        dialog.exec_()