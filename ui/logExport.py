# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui\logExport.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_logExport(object):
    def setupUi(self, logExport):
        logExport.setObjectName("logExport")
        logExport.resize(470, 301)
        self.verticalLayout = QtWidgets.QVBoxLayout(logExport)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(logExport)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.signalTree = QtWidgets.QTreeWidget(logExport)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.signalTree.sizePolicy().hasHeightForWidth())
        self.signalTree.setSizePolicy(sizePolicy)
        self.signalTree.setObjectName("signalTree")
        self.horizontalLayout.addWidget(self.signalTree)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(logExport)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.formatSelectCombo = QtWidgets.QComboBox(logExport)
        self.formatSelectCombo.setObjectName("formatSelectCombo")
        self.horizontalLayout_2.addWidget(self.formatSelectCombo)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.binSizeLabel = QtWidgets.QLabel(logExport)
        self.binSizeLabel.setObjectName("binSizeLabel")
        self.horizontalLayout_3.addWidget(self.binSizeLabel)
        self.binSizeSpin = QtWidgets.QSpinBox(logExport)
        self.binSizeSpin.setObjectName("binSizeSpin")
        self.horizontalLayout_3.addWidget(self.binSizeSpin)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.saveButton = QtWidgets.QPushButton(logExport)
        self.saveButton.setObjectName("saveButton")
        self.verticalLayout_2.addWidget(self.saveButton)
        self.uploadButton = QtWidgets.QPushButton(logExport)
        self.uploadButton.setObjectName("uploadButton")
        self.verticalLayout_2.addWidget(self.uploadButton)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(logExport)
        QtCore.QMetaObject.connectSlotsByName(logExport)

    def retranslateUi(self, logExport):
        _translate = QtCore.QCoreApplication.translate
        logExport.setWindowTitle(_translate("logExport", "Form"))
        self.label.setText(_translate("logExport", "Log Export"))
        self.signalTree.headerItem().setText(0, _translate("logExport", "Signal Selection"))
        self.label_2.setText(_translate("logExport", "Format:"))
        self.binSizeLabel.setText(_translate("logExport", "Bin Size (ms):"))
        self.saveButton.setText(_translate("logExport", "Save"))
        self.uploadButton.setText(_translate("logExport", "Upload"))
