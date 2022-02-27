from select import select
from display_widgets.widget_display import WidgetDisplay
from PyQt5 import QtWidgets, QtGui
import pyqtgraph as pg
import time
import utils

# Global view box that all x-axes link to
global view_box_link
view_box_link = None

class PlotWidget(WidgetDisplay):
    """ Plots signals versus time """
    
    def __init__(self, signals: dict, parent=None, fps=15, selected_signals=[]):
        super(PlotWidget, self).__init__(signals, labels=['Axis 1', 'Axis 2', 'Axis 3', 'Axis 4', 'Axis 5'], parent=parent)
        self.fps = fps

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Create plot widget
        self.pw = pg.PlotWidget()
        if not utils.dark_mode:
            self.pw.setBackground('w')
        self.layout.addWidget(self.pw)
        self.p1 = self.pw.plotItem

        self.view_boxes = []
        self.axes = []
        self.curves = []

        self.configureSignals(selected_signals)
        title = "" if len(self.current_signals) > 0 else "dbl click"
        self.initPlot(title=title)

    def initPlot(self, title="dbl click"):
        """ Resets plot, generates view boxes and axes for selected signals """

        # Clear existing settings
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

        # Generate view boxes and axes for each signal
        axis_col = 3
        for idx, signal in enumerate(self.current_signals):
            # signals connected by super class
            if idx == 0:
                global view_box_link
                if not view_box_link: view_box_link = self.p1
                else: 
                    self.p1.setXLink(view_box_link)
                # main plot item
                self.p1.setLabels(left=signal.signal_name + " " + signal.unit)
                self.p1.getAxis('left').setTextPen(signal.color)
                if not utils.dark_mode:
                    self.p1.getAxis('bottom').setTextPen(QtGui.QColor(0, 0, 0))
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
                self.axes[-1].setLabel(signal.signal_name + " " + signal.unit)
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

            st = time.perf_counter()
            # Set the axes to contain the most recent update
            most_recent = max([sig.last_update_time for sig in self.current_signals])
            self.pw.setXRange(max(most_recent-utils.plot_x_range_sec, 0), most_recent)
            # Replot each curve
            for idx, signal in enumerate(self.current_signals):
                with signal.data_lock:
                    self.curves[idx].setData(signal.times[:signal.length], signal.data[:signal.length], pen=signal.color)
            # Logging
            self.count += 1
            if (self.count % 20 == 0):
                self.count = 0
                utils.log(f"delta: {self.current_signals[0].signal_name}: {time.perf_counter() - st}")
    
    def updateViews(self):
        """ Updates other view boxes if main view box is moved """
        for box in self.view_boxes:
            box.setGeometry(self.p1.vb.sceneBoundingRect())

    def signalsChanged(self):
        """ Resets the plot each time signal is changed """
        self.initPlot(title="")
