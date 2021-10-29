from PyQt5 import QtWidgets
from communication.can_bus import BusSignal
from ui.signalPicker import Ui_signalPicker


class SignalPicker(QtWidgets.QDialog):
    """ Used to pick a signal based on node and message """

    def __init__(self, signals: dict, parent=None):
        super(SignalPicker, self).__init__(parent)
        self.ui = Ui_signalPicker()
        self.ui.setupUi(self)
        self.signals = signals
        self.chosen_signal = None

        # Signal connections
        self.ui.selectButton.clicked.connect(self.select)
        self.ui.nodeCombo.currentIndexChanged.connect(self.updateMsgCombo)
        self.ui.msgCombo.currentIndexChanged.connect(self.updateSigList)

        # Populate with items
        self.ui.nodeCombo.addItems(self.signals['Main'].keys())
        self.updateMsgCombo()
        self.updateSigList()

    def updateMsgCombo(self):
        """ Updates the message options """
        self.ui.msgCombo.clear()
        self.ui.msgCombo.addItems(self.signals['Main'][self.ui.nodeCombo.currentText()].keys())

    def updateSigList(self):
        """ Updates the list of signals """
        try:
            self.ui.signalList.clear()
            self.ui.signalList.addItems([sig[1].signal_name for sig in self.signals['Main'] \
                                        [self.ui.nodeCombo.currentText()]            \
                                        [self.ui.msgCombo.currentText()].items()])
        except KeyError:
            pass

    def select(self):
        """ Selects a signal """
        try:
            self.chosen_signal = self.signals['Main'][self.ui.nodeCombo.currentText()] \
                                            [self.ui.msgCombo.currentText()]          \
                                            [self.ui.signalList.currentItem().text()]
        except (KeyError, AttributeError):
            return
        self.accept() # closes dialog

    @staticmethod
    def getSignal(signals, parent=None) -> BusSignal:
        """ Used to create a signal picker, returns selected signal """
        picker = SignalPicker(signals, parent)
        picker.exec_()
        return picker.chosen_signal