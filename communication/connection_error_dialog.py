from PyQt5 import QtWidgets
from ui.connectionErrorDialog import Ui_ConnectionErrorDialog
import sys

class ConnectionErrorDialog(QtWidgets.QDialog):
    """ Used to retry connection and optionally enter a different ip address """

    def __init__(self, current_ip, parent=None):
        super(ConnectionErrorDialog, self).__init__(parent=parent)
        self.ui = Ui_ConnectionErrorDialog()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.cancelButton.clicked.connect(self.cancel)
        self.ui.retryButton.clicked.connect(self.retry)

        self.ui.addressText.setText(current_ip)

        self.chosen_ip = current_ip

    def retry(self):
        self.chosen_ip = self.ui.addressText.text()
        self.accept() # closes dialog
    
    def cancel(self):
        self.chosen_ip = None
        self.accept()
    
    @staticmethod
    def connectionError(current_ip, parent=None):
        """ Used when error connecting, returns new ip address """
        dialog = ConnectionErrorDialog(current_ip, parent=parent)
        dialog.exec_()
        return dialog.chosen_ip

        

