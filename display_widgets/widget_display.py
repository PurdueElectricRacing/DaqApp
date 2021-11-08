from PyQt5 import QtWidgets, QtGui
from display_widgets.signal_picker import MultiSignalPicker


class WidgetDisplay(QtWidgets.QWidget):
    """ Abstract class for selecting a signal to display when double clicked """

    def __init__(self, signals: dict, labels=['Axis 1'], parent=None):
        self.signals = signals
        self.current_signals = []
        self.labels = labels
        super(WidgetDisplay, self).__init__(parent)

    def updateDisplay(self):
        """ Called each time signal is updated"""
        pass

    def signalsChanged(self):
        """ Called on a signal change """
        pass

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent):
        """ Prompts widget configuration to select signals """
        # disconnect from existing signals
        for signal in self.current_signals:
            signal.disconnect(self.updateDisplay)

        signals = MultiSignalPicker.getSignals(self.signals, self.labels, self.current_signals, parent=self)

        # Don't do anything if you didn't pick anything
        if len(signals) == 0: return

        self.current_signals = signals

        for signal in self.current_signals:
            # TODO: if having all signals call updateDisplay is too intensive, able to have an update function per signal?
            signal.connect(self.updateDisplay)

        self.signalsChanged()
        return super().mouseDoubleClickEvent(a0)