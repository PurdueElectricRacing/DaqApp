from PyQt5 import QtWidgets
from ui.preferencesEditor import Ui_preferencesEditor
import utils


class PreferencesEditor(QtWidgets.QDialog):
    """ Used to edit preferences, mainly global configuration variables """

    def __init__(self, parent=None):
        super(PreferencesEditor, self).__init__(parent=parent)
        self.ui = Ui_preferencesEditor()
        self.ui.setupUi(self)

        # Signal connections
        self.ui.resetButton.clicked.connect(self.populateItems)
        self.ui.saveButton.clicked.connect(self.save)

        self.populateItems()

    
    def populateItems(self):
        """ Loads current settings into the widgets """
        self.ui.xRangeSpin.setValue(utils.plot_x_range_sec)
    
    def save(self):
        """ Updates settings and closes dialog """
        # Update variables
        utils.plot_x_range_sec = self.ui.xRangeSpin.value()

        self.accept() # close dialog
    
    @staticmethod
    def editPreferences(parent=None):
        """ Used to edit the preferences (opens dialog) """
        editor = PreferencesEditor(parent=parent)
        editor.exec_()