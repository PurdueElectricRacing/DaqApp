from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QLCDNumber, QLabel, QSizePolicy, QVBoxLayout
from display_widgets.widget_display import WidgetDisplay

class LcdDisplay(WidgetDisplay):
    """ LCD Display Widget """

    def __init__(self, signals: dict, parent=None):
        super(LcdDisplay, self).__init__(signals, parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Signal Title
        self.title = QLabel("Dbl Click")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setStyleSheet("font: bold 10px; text-decoration: underline;")
        self.layout.addWidget(self.title)

        # LCD Display
        self.lcd = QLCDNumber(self)
        self.lcd.setNumDigits(4)
        self.lcd.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.layout.addWidget(self.lcd)

        # Forces lcd closer to label
        self.verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout.addItem(self.verticalSpacer)

    def updateDisplay(self):
        """ Called each time signal value updated """
        self.lcd.display(self.current_signal.curr_val)
    
    def signalChanged(self):
        """ Changes signal name label """
        self.title.setText(self.current_signal.signal_name)
