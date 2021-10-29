import sys
import matplotlib
from display_widgets.widget_display import WidgetDisplay
from PyQt5 import QtCore, QtGui, QtWidgets
from qwt import QwtPlot, QwtPlotCurve
import time

# TODO: plot multiple variables on top of each other
# TODO: play and pause, (ability to scroll back in time)

class PlotWidget(WidgetDisplay):
    """ Plots a signal versus time """
    
    def __init__(self, signals: dict, parent=None, fps=15):
        super(PlotWidget, self).__init__(signals, parent)
        self.fps = fps

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.dataPlot = QwtPlot()
        self.layout.addWidget(self.dataPlot)
        self.initPlot()

    def initPlot(self, title="dbl click"):
        """ Resets plot """
        self.xData = []
        self.yData = []
        self.dataPlot.detachItems()
        self.start_time = 0
        self.last_update_time = 0
        self.curve = QwtPlotCurve(title)
        self.curve.setPen(QtGui.QColor(255, 255, 255))
        self.curve.setData(self.xData, self.yData)
        self.curve.attach(self.dataPlot)
        self.dataPlot.replot()
        self.dataPlot.setTitle(title)

    def updateDisplay(self):
        """ Called each time signal value updated, update plot at fps """
        hist = 3000
        if self.start_time == 0: self.start_time = self.current_signal.last_update_time
        self.xData.append(self.current_signal.last_update_time - self.start_time)
        self.yData.append(self.current_signal.curr_val)
        self.xData = self.xData[-hist:]
        self.yData = self.yData[-hist:]

        # Redraw plot at fps
        curr = time.time()
        if curr - self.last_update_time > 1.0/self.fps:
            self.last_update_time = curr
            self.curve.setData(self.xData, self.yData)
            self.dataPlot.replot()

    def signalChanged(self):
        """ Resets the plot each time signal is changed """
        self.initPlot(title=self.current_signal.signal_name)
