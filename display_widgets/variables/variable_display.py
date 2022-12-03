from PyQt5 import QtWidgets, QtGui
from communication.can_bus import BusSignal
from ui.variable import Ui_variableDisplay
import utils


class VariableDisplay(QtWidgets.QWidget):
    """ Used to display a generic value with name and units """

    def __init__(self, parent=None):
        super(VariableDisplay, self).__init__(parent)
        self.ui = Ui_variableDisplay()
        self.ui.setupUi(self)
        parent = self.parentWidget()
        for i in range(3):
            try:
                parent.registerVariable(self)
                break
            except AttributeError:
                parent = parent.parentWidget()


    def setAlignment(self, a):
        """ required for promotion from label """
        pass

    def setText(self, txt):
        self.ui.Name.setText(txt)

    def setFont(self, font):
        self.ui.Name.setFont(font)
        self.ui.Units.setFont(font)
        self.ui.Value.setFont(font)

    def setUnits(self, units):
        self.ui.Units.setText(units)

    def setValue(self, val):
        self.ui.Value.setText(str(val))

    def setName(self, name):
        self.ui.Name.setText(name)

    def updatePeriodic(self):
        """ called by parent each time display update desired """
        pass