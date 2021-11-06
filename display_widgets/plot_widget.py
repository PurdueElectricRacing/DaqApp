import sys
import matplotlib
from display_widgets.widget_display import WidgetDisplay
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import time

# TODO: plot multiple variables on top of each other
# TODO: resize with mouse

class PlotWidget(WidgetDisplay):
    """ Plots a signal versus time """
    
    def __init__(self, signals: dict, parent=None, fps=15):
        super(PlotWidget, self).__init__(signals, labels=['Axis 1', 'Axis 2', 'Axis 3', 'Axis 4', 'Axis 5'], parent=parent)
        self.fps = fps

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.x_range = 10 

        self.pw = pg.PlotWidget()
        self.layout.addWidget(self.pw)
        self.p1 = self.pw.plotItem

        #self.dataPlot = pg.PlotWidget()
        #self.layout.addWidget(self.dataPlot)

        self.view_boxes = []
        self.axes = []
        self.curves = []

        self.initPlot()

        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.updateDisplay)
        # self.timer.setInterval(1000/fps)

    def initPlot(self, title="dbl click"):
        """ Resets plot """
        self.last_update_time = 0
        self.pw.clear()
        self.pw.setDownsampling(mode='peak')
        self.pw.setClipToView(True)
        self.pw.setTitle(title)

        for axis in self.axes:
            self.p1.layout.removeItem(axis)
        for vb in self.view_boxes:
            self.p1.scene().removeItem(vb)

        self.view_boxes = []
        self.axes = []
        self.curves = []

        axis_col = 3

        for idx, signal in enumerate(self.current_signals):
            # signals connected by super class
            if idx == 0:
                # main plot item
                self.p1.setLabels(left=signal.signal_name)
                self.p1.getAxis('left').setTextPen(signal.color)
                self.curves.append(self.p1.plot())
            else:
                self.view_boxes.append(pg.ViewBox())
                self.p1.scene().addItem(self.view_boxes[-1])

                self.axes.append(pg.AxisItem('right'))
                self.p1.layout.addItem(self.axes[-1], 2, axis_col)
                # link axis with view box
                self.axes[-1].linkToView(self.view_boxes[-1])

                # link view box with main plot viewbox
                self.view_boxes[-1].setXLink(self.p1)
                axis_col += 1

                # add curve to view box
                self.curves.append(pg.PlotCurveItem(pen=signal.color))
                self.view_boxes[-1].addItem(self.curves[-1])

                # configure axis settings
                self.axes[-1].setLabel(signal.signal_name)
                self.axes[-1].setTextPen(signal.color)
        
        self.p1.vb.sigResized.connect(self.updateViews)
        self.updateViews()


    count = 0
    def updateDisplay(self):
        """ Called each time signal value updated, update plot at fps """

        # Redraw plot at fps
        curr = time.time()
        if curr - self.last_update_time > 1.0/self.fps:
            self.last_update_time = curr
            # TODO: DataAxisItem for time
            # TODO: set XLink (see ViewBoxFeatures.py to link the x-axes)
            # TODO: use dockarea

            st = time.perf_counter()
            self.pw.setXRange(max(self.current_signals[0].last_update_time-self.x_range, 0), self.current_signals[0].last_update_time)
            for idx, signal in enumerate(self.current_signals):
                with signal.data_lock:
                    self.curves[idx].setData(signal.times[:signal.length], signal.data[:signal.length], pen=signal.color)
            self.count += 1
            if (self.count % 20 == 0):
                self.count = 0
                print(f"delta: {self.current_signals[0].signal_name}: {time.perf_counter() - st}")
    
    def updateViews(self):
        for box in self.view_boxes:
            box.setGeometry(self.p1.vb.sceneBoundingRect())

    def signalsChanged(self):
        """ Resets the plot each time signal is changed """
        self.initPlot(title="")
