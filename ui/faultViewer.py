# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'faultViewer.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FaultViewer(object):
    def setupUi(self, FaultViewer):
        FaultViewer.setObjectName("FaultViewer")
        FaultViewer.resize(783, 415)
        self.verticalLayout = QtWidgets.QVBoxLayout(FaultViewer)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(FaultViewer)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.MainDivider = QtWidgets.QHBoxLayout()
        self.MainDivider.setObjectName("MainDivider")
        self.nodeStatus = QtWidgets.QVBoxLayout()
        self.nodeStatus.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.nodeStatus.setContentsMargins(-1, -1, 0, -1)
        self.nodeStatus.setObjectName("nodeStatus")
        self.nodeStatLabel = QtWidgets.QLabel(FaultViewer)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setUnderline(False)
        font.setWeight(75)
        self.nodeStatLabel.setFont(font)
        self.nodeStatLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.nodeStatLabel.setObjectName("nodeStatLabel")
        self.nodeStatus.addWidget(self.nodeStatLabel)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.nodeStatus.addItem(spacerItem)
        self.MainDivider.addLayout(self.nodeStatus)
        self.InfoLayer = QtWidgets.QVBoxLayout()
        self.InfoLayer.setObjectName("InfoLayer")
        self.InfoLayer2 = QtWidgets.QHBoxLayout()
        self.InfoLayer2.setObjectName("InfoLayer2")
        self.InfoSplit = QtWidgets.QVBoxLayout()
        self.InfoSplit.setObjectName("InfoSplit")
        self.Info = QtWidgets.QTreeWidget(FaultViewer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Info.sizePolicy().hasHeightForWidth())
        self.Info.setSizePolicy(sizePolicy)
        self.Info.setAutoFillBackground(True)
        self.Info.setObjectName("Info")
        self.Info.headerItem().setText(0, "1")
        self.Info.header().setDefaultSectionSize(100)
        self.InfoSplit.addWidget(self.Info)
        self.label_2 = QtWidgets.QLabel(FaultViewer)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.InfoSplit.addWidget(self.label_2)
        self.NodeSelect = QtWidgets.QComboBox(FaultViewer)
        self.NodeSelect.setObjectName("NodeSelect")
        self.InfoSplit.addWidget(self.NodeSelect)
        self.label_3 = QtWidgets.QLabel(FaultViewer)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.InfoSplit.addWidget(self.label_3)
        self.MessageConfigurator = QtWidgets.QHBoxLayout()
        self.MessageConfigurator.setObjectName("MessageConfigurator")
        self.FaultStatusSelect = QtWidgets.QVBoxLayout()
        self.FaultStatusSelect.setObjectName("FaultStatusSelect")
        self.Zero = QtWidgets.QRadioButton(FaultViewer)
        self.Zero.setObjectName("Zero")
        self.FaultStatusSelect.addWidget(self.Zero)
        self.One = QtWidgets.QRadioButton(FaultViewer)
        self.One.setObjectName("One")
        self.FaultStatusSelect.addWidget(self.One)
        self.MessageConfigurator.addLayout(self.FaultStatusSelect)
        self.FaultSelect = QtWidgets.QComboBox(FaultViewer)
        self.FaultSelect.setObjectName("FaultSelect")
        self.MessageConfigurator.addWidget(self.FaultSelect)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.MessageSend = QtWidgets.QPushButton(FaultViewer)
        self.MessageSend.setObjectName("MessageSend")
        self.verticalLayout_3.addWidget(self.MessageSend)
        self.ReturnSend = QtWidgets.QPushButton(FaultViewer)
        self.ReturnSend.setObjectName("ReturnSend")
        self.verticalLayout_3.addWidget(self.ReturnSend)
        self.MessageConfigurator.addLayout(self.verticalLayout_3)
        self.MessageConfigurator.setStretch(0, 1)
        self.MessageConfigurator.setStretch(1, 5)
        self.InfoSplit.addLayout(self.MessageConfigurator)
        self.InfoLayer2.addLayout(self.InfoSplit)
        self.InfoLayer.addLayout(self.InfoLayer2)
        self.InfoLayer.setStretch(0, 1)
        self.MainDivider.addLayout(self.InfoLayer)
        self.MainDivider.setStretch(0, 1)
        self.MainDivider.setStretch(1, 6)
        self.verticalLayout.addLayout(self.MainDivider)

        self.retranslateUi(FaultViewer)
        QtCore.QMetaObject.connectSlotsByName(FaultViewer)

    def retranslateUi(self, FaultViewer):
        _translate = QtCore.QCoreApplication.translate
        FaultViewer.setWindowTitle(_translate("FaultViewer", "Form"))
        self.label.setText(_translate("FaultViewer", "Fault Viewer"))
        self.nodeStatLabel.setText(_translate("FaultViewer", "Node Status"))
        self.label_2.setText(_translate("FaultViewer", "Select a Node"))
        self.label_3.setText(_translate("FaultViewer", "Select a Fault"))
        self.Zero.setText(_translate("FaultViewer", "0"))
        self.One.setText(_translate("FaultViewer", "1"))
        self.MessageSend.setText(_translate("FaultViewer", "Force"))
        self.ReturnSend.setText(_translate("FaultViewer", "Return Control"))
