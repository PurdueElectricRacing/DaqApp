# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui\mainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuEdit_2 = QtWidgets.QMenu(self.menubar)
        self.menuEdit_2.setObjectName("menuEdit_2")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionVariable_Editor = QtWidgets.QAction(MainWindow)
        self.actionVariable_Editor.setCheckable(True)
        self.actionVariable_Editor.setChecked(False)
        self.actionVariable_Editor.setObjectName("actionVariable_Editor")
        self.actionFrame_Viewer = QtWidgets.QAction(MainWindow)
        self.actionFrame_Viewer.setCheckable(True)
        self.actionFrame_Viewer.setChecked(True)
        self.actionFrame_Viewer.setObjectName("actionFrame_Viewer")
        self.actionLCD = QtWidgets.QAction(MainWindow)
        self.actionLCD.setObjectName("actionLCD")
        self.actionDashboard = QtWidgets.QAction(MainWindow)
        self.actionDashboard.setCheckable(True)
        self.actionDashboard.setObjectName("actionDashboard")
        self.actionPlot = QtWidgets.QAction(MainWindow)
        self.actionPlot.setObjectName("actionPlot")
        self.actionMatPlot = QtWidgets.QAction(MainWindow)
        self.actionMatPlot.setObjectName("actionMatPlot")
        self.actionRemoveWidget = QtWidgets.QAction(MainWindow)
        self.actionRemoveWidget.setObjectName("actionRemoveWidget")
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionLog_Exporter = QtWidgets.QAction(MainWindow)
        self.actionLog_Exporter.setCheckable(True)
        self.actionLog_Exporter.setObjectName("actionLog_Exporter")
        self.actionImport_log = QtWidgets.QAction(MainWindow)
        self.actionImport_log.setObjectName("actionImport_log")
        self.actionLoad_View = QtWidgets.QAction(MainWindow)
        self.actionLoad_View.setObjectName("actionLoad_View")
        self.actionSave_View = QtWidgets.QAction(MainWindow)
        self.actionSave_View.setObjectName("actionSave_View")
        self.actionCell_Viewer = QtWidgets.QAction(MainWindow)
        self.actionCell_Viewer.setCheckable(True)
        self.actionCell_Viewer.setObjectName("actionCell_Viewer")
        self.actionBootloader = QtWidgets.QAction(MainWindow)
        self.actionBootloader.setCheckable(True)
        self.actionBootloader.setObjectName("actionBootloader")
        self.actionFaultViewer = QtWidgets.QAction(MainWindow)
        self.actionFaultViewer.setCheckable(True)
        self.actionFaultViewer.setObjectName("actionFaultViewer")
        self.menuHelp.addAction(self.actionAbout)
        self.menuView.addAction(self.actionVariable_Editor)
        self.menuView.addAction(self.actionFrame_Viewer)
        self.menuView.addAction(self.actionLog_Exporter)
        self.menuView.addAction(self.actionCell_Viewer)
        self.menuView.addAction(self.actionBootloader)
        self.menuView.addAction(self.actionFaultViewer)
        self.menuEdit.addAction(self.actionLCD)
        self.menuEdit.addAction(self.actionPlot)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionRemoveWidget)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionLoad_View)
        self.menuEdit.addAction(self.actionSave_View)
        self.menuEdit_2.addAction(self.actionPreferences)
        self.menuFile.addAction(self.actionImport_log)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit_2.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "DAQ"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.menuView.setTitle(_translate("MainWindow", "View"))
        self.menuEdit.setTitle(_translate("MainWindow", "Widgets"))
        self.menuEdit_2.setTitle(_translate("MainWindow", "Edit"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
        self.actionVariable_Editor.setText(_translate("MainWindow", "Variable Editor"))
        self.actionFrame_Viewer.setText(_translate("MainWindow", "Frame Viewer"))
        self.actionLCD.setText(_translate("MainWindow", "LCD"))
        self.actionDashboard.setText(_translate("MainWindow", "Dashboard"))
        self.actionPlot.setText(_translate("MainWindow", "Plot"))
        self.actionMatPlot.setText(_translate("MainWindow", "MatPlot"))
        self.actionRemoveWidget.setText(_translate("MainWindow", "Remove"))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences"))
        self.actionLog_Exporter.setText(_translate("MainWindow", "Log Exporter"))
        self.actionImport_log.setText(_translate("MainWindow", "Import Log"))
        self.actionLoad_View.setText(_translate("MainWindow", "Load View"))
        self.actionSave_View.setText(_translate("MainWindow", "Save View"))
        self.actionCell_Viewer.setText(_translate("MainWindow", "Cell Viewer"))
        self.actionBootloader.setText(_translate("MainWindow", "Bootloader"))
        self.actionFaultViewer.setText(_translate("MainWindow", "Fault Viewer"))
