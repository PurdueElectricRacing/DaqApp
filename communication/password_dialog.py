from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialogButtonBox
from ui.passwordDialog import Ui_Dialog
import sys

class PasswordDialog(QtWidgets.QDialog):
    def __init__(self, password, setText, parent=None):
        super(PasswordDialog, self).__init__(parent=parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.buttonBox.clicked.connect(self.handleClick)
        if (setText):
            self.ui.label.setText("Password Rejected. Please Try Again:")

        self.chosen_password = password

    #     self.ui.dismiss.clicked.connect(self.closeWindow)

    def handleClick(self, button):
        role = self.ui.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.RejectRole:
            self.chosen_password = None
            print("reject")
            self.accept()
        if role == QDialogButtonBox.AcceptRole:
            self.chosen_password = self.ui.lineEdit.text()
            print("accept")
            self.accept()

    @staticmethod
    def setText(password, parent=None):
        dialog = PasswordDialog(password, True, parent=parent)
        dialog.exec_()
        return dialog.chosen_password

    @staticmethod
    def promptPassword(password, parent=None):
        """ Used when error connecting, returns new ip address """
        dialog = PasswordDialog(password, False, parent=parent)
        dialog.exec_()
        return dialog.chosen_password