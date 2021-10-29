import sys
import matplotlib

from display_widgets.widget_display import WidgetDisplay
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import time

class MatPlotWidget(WidgetDisplay):
    
    def __init__(self, signals:dict, parent=None, width=5, height=4, dpi=100, fps=15):
        super(MatPlotWidget, self).__init__(signals, parent)

        self.fps = fps

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.toolbar = NavigationToolbar(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.start_time = 0
        self.last_update_time = 0

        self.xData = []
        self.yData = []

    def replot(self):
        #f.axes.plot(self.xData, self.yData)
        self.axes.clear()
        self.axes.plot(self.xData, self.yData)
        self.canvas.draw()


    def updateDisplay(self):
        hist = 3000
        if self.start_time == 0: self.start_time = self.current_signal.last_update_time
        self.xData.append(self.current_signal.last_update_time - self.start_time)
        self.yData.append(self.current_signal.curr_val)
        self.xData = self.xData[-hist:]
        self.yData = self.yData[-hist:]

        curr = time.time()
        if curr - self.last_update_time > 1.0/self.fps:
            self.last_update_time = curr
            self.replot()

    def signalChanged(self):
        self.fig.suptitle(self.current_signal.signal_name)
        self.axes.set_xlabel("Time?")
        self.canvas.draw()
