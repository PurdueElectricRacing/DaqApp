from PyQt5 import QtWidgets
from ui.preferencesEditor import Ui_preferencesEditor
import utils


class PreferencesEditor(QtWidgets.QDialog):
    """ Used to edit preferences, mainly global configuration variables """

    def __init__(self, varEdit, parent=None):
        super(PreferencesEditor, self).__init__(parent=parent)
        self.ui = Ui_preferencesEditor()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.resetButton.clicked.connect(self.populateItems)
        self.ui.saveButton.clicked.connect(self.save)

        self.varEdit = varEdit

        self.populateItems()
    
    def populateItems(self):
        """ Loads current settings into the widgets """
        self.ui.xRangeSpin.setValue(utils.plot_x_range_sec)

        bus_list = list(utils.signals.keys())
        self.ui.busCombo.addItems(bus_list)
        try:
            self.ui.busCombo.setCurrentIndex(bus_list.index(utils.b_str))
        except:
            pass # lol
    
    def save(self):
        """ Updates settings and closes dialog """
        # Update variables
        utils.plot_x_range_sec = self.ui.xRangeSpin.value()
        utils.b_str = self.ui.busCombo.currentText()

        self.varEdit.updateNodeList()
        self.accept() # close dialog
    
    @staticmethod
    def editPreferences(varEdit, parent=None):
        """ Used to edit the preferences (opens dialog) """
        editor = PreferencesEditor(varEdit, parent=parent)
        editor.exec_()