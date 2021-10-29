from PyQt5 import QtWidgets, QtGui
from display_widgets.signal_picker import SignalPicker


class WidgetDisplay(QtWidgets.QWidget):
    """ Abstract class for selecting a signal to display when double clicked """

    signals = {}
    current_signal = None

    def __init__(self, signals: dict, parent=None):
        self.signals = signals
        super(WidgetDisplay, self).__init__(parent)

    def updateDisplay(self):
        pass

    def signalChanged(self):
        pass

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent):
        signal = SignalPicker.getSignal(self.signals, self)
        if signal:
            if self.current_signal: self.current_signal.disconnect()
            self.current_signal = signal
            self.current_signal.connect(self.updateDisplay)
            self.signalChanged()
        return super().mouseDoubleClickEvent(a0)