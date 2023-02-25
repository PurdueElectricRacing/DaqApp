# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui\chargeView2.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_chargeViewer(object):
    def setupUi(self, chargeViewer):
        chargeViewer.setObjectName("chargeViewer")
        chargeViewer.resize(915, 622)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(chargeViewer.sizePolicy().hasHeightForWidth())
        chargeViewer.setSizePolicy(sizePolicy)
        chargeViewer.setToolTip("")
        self.verticalLayout = QtWidgets.QVBoxLayout(chargeViewer)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = DAQVariableDisplay(chargeViewer)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.label_3 = DAQVariableDisplay(chargeViewer)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.label_4 = CANVariableDisplay(chargeViewer)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.label_5 = DAQVariableDisplay(chargeViewer)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)

        self.retranslateUi(chargeViewer)
        QtCore.QMetaObject.connectSlotsByName(chargeViewer)

    def retranslateUi(self, chargeViewer):
        _translate = QtCore.QCoreApplication.translate
        chargeViewer.setWindowTitle(_translate("chargeViewer", "Form"))
        self.label_2.setText(_translate("chargeViewer", "TEST_NODE.daq_response_TEST_NODE.test_var2"))
        self.label_3.setText(_translate("chargeViewer", "TEST_NODE.daq_response_TEST_NODE.green_on"))
        self.label_4.setText(_translate("chargeViewer", "TEST_NODE.test_msg2.test_sig2"))
        self.label_5.setText(_translate("chargeViewer", "TEST_NODE.daq_response_TEST_NODE.trim"))
from display_widgets.variables.can_variable_display import CANVariableDisplay
from display_widgets.variables.daq_variable_display import DAQVariableDisplay