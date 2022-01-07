from PyQt5 import QtWidgets, QtGui
from communication.can_bus import BusSignal
from ui.signalPicker import Ui_signalPicker
import utils


class SignalPicker(QtWidgets.QDialog):
    """ Used to pick a signal based on node and message """

    def __init__(self, signals: dict, curr_signal:BusSignal, parent=None):
        super(SignalPicker, self).__init__(parent)
        self.ui = Ui_signalPicker()
        self.ui.setupUi(self)
        self.signals = signals
        self.chosen_signal = None

        # Signal connections
        self.ui.selectButton.clicked.connect(self.select)
        self.ui.nodeCombo.currentIndexChanged.connect(self.updateMsgCombo)
        self.ui.msgCombo.currentIndexChanged.connect(self.updateSigList)
        self.ui.colorButton.clicked.connect(self.getColor)

        # Populate with items
        self.ui.nodeCombo.addItems(self.signals[utils.b_str].keys())

        self.color = QtGui.QColor(255, 255, 255)

        # Set current selection
        if curr_signal != None:
            self.ui.nodeCombo.setCurrentText(curr_signal.node_name)
            self.color = curr_signal.color
            self.ui.colorButton.setStyleSheet(f"background-color: {self.color.name()}")

        self.updateMsgCombo()
        if curr_signal != None: self.ui.msgCombo.setCurrentText(curr_signal.message_name) 

        self.updateSigList()
        if curr_signal != None: self.ui.signalList.setCurrentRow(list(self.signals[utils.b_str][curr_signal.node_name][curr_signal.message_name].keys()).index(curr_signal.signal_name))

    def updateMsgCombo(self):
        """ Updates the message options """
        self.ui.msgCombo.clear()
        self.ui.msgCombo.addItems(self.signals[utils.b_str][self.ui.nodeCombo.currentText()].keys())

    def updateSigList(self):
        """ Updates the list of signals """
        try:
            self.ui.signalList.clear()
            self.ui.signalList.addItems([sig[1].signal_name for sig in self.signals[utils.b_str] \
                                        [self.ui.nodeCombo.currentText()]            \
                                        [self.ui.msgCombo.currentText()].items()] + ['None'])
        except KeyError:
            pass
    
    def getColor(self):
        """ Prompts user to select a color for the signal """
        self.color = QtWidgets.QColorDialog.getColor()
        self.ui.colorButton.setStyleSheet(f"background-color: {self.color.name()}")


    def select(self):
        """ Selects a signal """
        try:
            if self.ui.signalList.currentItem().text() == 'None':
                self.chosen_signal = None
            else:
                self.chosen_signal = self.signals[utils.b_str][self.ui.nodeCombo.currentText()] \
                                            [self.ui.msgCombo.currentText()]          \
                                            [self.ui.signalList.currentItem().text()]
        except (KeyError, AttributeError):
            return
        self.accept() # closes dialog

    @staticmethod
    def getSignal(signals, curr_signal, parent=None):
        """ Used to create a signal picker, returns selected signal """
        picker = SignalPicker(signals, curr_signal, parent)
        picker.exec_()
        if picker.chosen_signal: picker.chosen_signal.color = picker.color
        return picker.chosen_signal
    
class MultiSignalPicker(QtWidgets.QDialog):
    """ Used to pick multiple signals to correspond to defined labels """

    def __init__(self, signals:dict, labels, current_signals, requires_all=False, parent=None):
        super(MultiSignalPicker, self).__init__(parent)
        self.signals = signals
        self.labels = labels
        self.requires_all = requires_all # does it require signals for all labels

        # Setup ui
        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        # Signal selection buttons and labels
        self.horizontal_layouts = []
        self.label_objects = []
        self.button_objects = []
        self.current_signals = current_signals

        for idx, label in enumerate(self.labels):
            self.horizontal_layouts.append(QtWidgets.QHBoxLayout())
            self.label_objects.append(QtWidgets.QLabel(label, parent=self))
            self.horizontal_layouts[-1].addWidget(self.label_objects[-1])
            self.button_objects.append(QtWidgets.QPushButton(text="Choose signal", parent=self))
            self.horizontal_layouts[-1].addWidget(self.button_objects[-1])
            self.button_objects[-1].clicked.connect(self.makeCallButtonClicked(idx))
            if idx != 0: self.button_objects[-1].setDisabled(True)
            self.verticalLayout.addLayout(self.horizontal_layouts[-1])
        
        # update buttons to match current signals
        for idx, signal in enumerate(self.current_signals):
            self.button_objects[idx].setText(signal.signal_name)
            self.button_objects[idx].setStyleSheet(f"background-color: {signal.color.name()}")
            if idx+1 < len(self.button_objects): self.button_objects[idx+1].setDisabled(False)

        # Select button
        self.selectButton = QtWidgets.QPushButton(self, text="Select")
        self.verticalLayout.addWidget(self.selectButton)
        self.selectButton.clicked.connect(self.select)
    
    def buttonClicked(self, idx):
        """ Callback for signal select button, prompt signal selection """
        prev_sig = None
        if idx < len(self.current_signals): prev_sig = self.current_signals[idx]
        signal = SignalPicker.getSignal(self.signals, prev_sig, self)
        if not signal: 
            if len(self.current_signals) - 1 == idx:
                self.current_signals.pop()
                self.button_objects[idx].setText("Choose signal")
            return
        if len(self.current_signals) <= idx: self.current_signals.append(signal)
        else: self.current_signals[idx] = signal

        # Update button to match selected signal
        self.button_objects[idx].setText(signal.signal_name)
        self.button_objects[idx].setStyleSheet(f"background-color: {signal.color.name()}")
        if idx+1 < len(self.button_objects): self.button_objects[idx+1].setDisabled(False)

    def makeCallButtonClicked(self, idx):
        """ function factory :(, allows for all signal buttons to use same callback """
        def callButtonClicked():
            self.buttonClicked(idx)
        return callButtonClicked
    
    def select(self):
        """ checks if selection requirements met and closes dialog """
        if not self.requires_all or len(self.signals) == len(self.labels):
            self.accept()
    
    @staticmethod
    def getSignals(signals, labels, current_signals, requires_all=False, parent=None):
        """ Prompts user to select signals to correspond to predefined labels """
        multiPicker = MultiSignalPicker(signals, labels, current_signals, requires_all=requires_all, parent=parent)
        multiPicker.exec_()
        return multiPicker.current_signals
