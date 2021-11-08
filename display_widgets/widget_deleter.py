from PyQt5 import QtWidgets
from PyQt5.QtCore import QModelIndex
from ui.widgetDeleter import Ui_widgetDelete

class WidgetDeleter(QtWidgets.QDialog):
    """ Used to select a widget to delete """

    def __init__(self, widget_list, parent=None):
        super(WidgetDeleter, self).__init__(parent)
        self.ui = Ui_widgetDelete()
        self.ui.setupUi(self)
        self.widget_list = widget_list

        self.text_list = []
        for w in self.widget_list:
            if len(w.current_signals) > 0:
                self.text_list.append(f"{w.__class__.__name__} with {w.current_signals[0].signal_name}")
            else:
                self.text_list.append(f"Untitled {w.__class__.__name__}")

        self.widget_selection = []

        # Signal Connections
        self.ui.selectBtn.clicked.connect(self.select)

        # populate with items
        self.ui.widgetList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.ui.widgetList.addItems(self.text_list)
    
    def select(self):
        """ creates list of display widgets to delete and closes dialog """
        self.widget_selection = []
        for idx in self.ui.widgetList.selectedIndexes():
            self.widget_selection.append(self.widget_list[idx.row()])
        self.accept() # closes dialog

    @staticmethod
    def getWidgets(widgets, parent=None):
        """ Prompts user to select widgets to delete """
        deleter = WidgetDeleter(widgets, parent=parent)
        deleter.exec_()
        return deleter.widget_selection

    


