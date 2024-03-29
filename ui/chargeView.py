# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui\chargeView.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_chargeViewer(object):
    def setupUi(self, chargeViewer):
        chargeViewer.setObjectName("chargeViewer")
        chargeViewer.resize(1484, 622)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(chargeViewer.sizePolicy().hasHeightForWidth())
        chargeViewer.setSizePolicy(sizePolicy)
        chargeViewer.setToolTip("")
        self.horizontalLayout = QtWidgets.QHBoxLayout(chargeViewer)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_4 = QtWidgets.QGroupBox(chargeViewer)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_4.setFont(font)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_17 = DAQVariableDisplay(self.groupBox_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_17.setFont(font)
        self.label_17.setObjectName("label_17")
        self.verticalLayout_4.addWidget(self.label_17)
        self.label_18 = DAQVariableDisplay(self.groupBox_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_18.setFont(font)
        self.label_18.setObjectName("label_18")
        self.verticalLayout_4.addWidget(self.label_18)
        self.label_19 = DAQVariableDisplay(self.groupBox_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_19.setFont(font)
        self.label_19.setObjectName("label_19")
        self.verticalLayout_4.addWidget(self.label_19)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.horizontalLayout.addWidget(self.groupBox_4)
        self.groupBox_3 = QtWidgets.QGroupBox(chargeViewer)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_31 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_31.setFont(font)
        self.label_31.setObjectName("label_31")
        self.verticalLayout_3.addWidget(self.label_31)
        self.label_30 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_30.setFont(font)
        self.label_30.setObjectName("label_30")
        self.verticalLayout_3.addWidget(self.label_30)
        self.label_14 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_14.setFont(font)
        self.label_14.setObjectName("label_14")
        self.verticalLayout_3.addWidget(self.label_14)
        self.label_11 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_3.addWidget(self.label_11)
        self.label_15 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_15.setFont(font)
        self.label_15.setObjectName("label_15")
        self.verticalLayout_3.addWidget(self.label_15)
        self.label_16 = CANVariableDisplay(self.groupBox_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_16.setFont(font)
        self.label_16.setObjectName("label_16")
        self.verticalLayout_3.addWidget(self.label_16)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem1)
        self.horizontalLayout.addWidget(self.groupBox_3)
        self.groupBox_5 = QtWidgets.QGroupBox(chargeViewer)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_5.setFont(font)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_20 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_20.setFont(font)
        self.label_20.setObjectName("label_20")
        self.verticalLayout_5.addWidget(self.label_20)
        self.label_23 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_23.setFont(font)
        self.label_23.setObjectName("label_23")
        self.verticalLayout_5.addWidget(self.label_23)
        self.label_24 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_24.setFont(font)
        self.label_24.setObjectName("label_24")
        self.verticalLayout_5.addWidget(self.label_24)
        self.label_12 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.verticalLayout_5.addWidget(self.label_12)
        self.label_21 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_21.setFont(font)
        self.label_21.setObjectName("label_21")
        self.verticalLayout_5.addWidget(self.label_21)
        self.label_22 = CANVariableDisplay(self.groupBox_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_22.setFont(font)
        self.label_22.setObjectName("label_22")
        self.verticalLayout_5.addWidget(self.label_22)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem2)
        self.horizontalLayout.addWidget(self.groupBox_5)
        self.groupBox_6 = QtWidgets.QGroupBox(chargeViewer)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_6.setFont(font)
        self.groupBox_6.setObjectName("groupBox_6")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox_6)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_25 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_25.setFont(font)
        self.label_25.setObjectName("label_25")
        self.verticalLayout_6.addWidget(self.label_25)
        self.label_26 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_26.setFont(font)
        self.label_26.setObjectName("label_26")
        self.verticalLayout_6.addWidget(self.label_26)
        self.label_27 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_27.setFont(font)
        self.label_27.setObjectName("label_27")
        self.verticalLayout_6.addWidget(self.label_27)
        self.label_13 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_13.setFont(font)
        self.label_13.setObjectName("label_13")
        self.verticalLayout_6.addWidget(self.label_13)
        self.label_28 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.verticalLayout_6.addWidget(self.label_28)
        self.label_29 = CANVariableDisplay(self.groupBox_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_29.setFont(font)
        self.label_29.setObjectName("label_29")
        self.verticalLayout_6.addWidget(self.label_29)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem3)
        self.horizontalLayout.addWidget(self.groupBox_6)
        self.groupBox_7 = QtWidgets.QGroupBox(chargeViewer)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_7.setFont(font)
        self.groupBox_7.setObjectName("groupBox_7")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.groupBox_7)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_32 = CANVariableDisplay(self.groupBox_7)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_32.setFont(font)
        self.label_32.setObjectName("label_32")
        self.verticalLayout_7.addWidget(self.label_32)
        self.label_33 = CANVariableDisplay(self.groupBox_7)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_33.setFont(font)
        self.label_33.setObjectName("label_33")
        self.verticalLayout_7.addWidget(self.label_33)
        self.label_34 = CANVariableDisplay(self.groupBox_7)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_34.setFont(font)
        self.label_34.setObjectName("label_34")
        self.verticalLayout_7.addWidget(self.label_34)
        self.label_35 = CANVariableDisplay(self.groupBox_7)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_35.setFont(font)
        self.label_35.setObjectName("label_35")
        self.verticalLayout_7.addWidget(self.label_35)
        self.label_36 = CANVariableDisplay(self.groupBox_7)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_36.setFont(font)
        self.label_36.setObjectName("label_36")
        self.verticalLayout_7.addWidget(self.label_36)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem4)
        self.horizontalLayout.addWidget(self.groupBox_7)

        self.retranslateUi(chargeViewer)
        QtCore.QMetaObject.connectSlotsByName(chargeViewer)

    def retranslateUi(self, chargeViewer):
        _translate = QtCore.QCoreApplication.translate
        chargeViewer.setWindowTitle(_translate("chargeViewer", "Form"))
        self.groupBox_4.setTitle(_translate("chargeViewer", "Charge Control"))
        self.label_17.setText(_translate("chargeViewer", "Precharge.daq_response_PRECHARGE.charge_request_user"))
        self.label_18.setText(_translate("chargeViewer", "Precharge.daq_response_PRECHARGE.user_charge_current_request"))
        self.label_19.setText(_translate("chargeViewer", "Precharge.daq_response_PRECHARGE.user_charge_voltage_request"))
        self.groupBox_3.setTitle(_translate("chargeViewer", "Charge Status"))
        self.label_31.setText(_translate("chargeViewer", "Precharge.precharge_hb.BMS"))
        self.label_30.setText(_translate("chargeViewer", "Precharge.precharge_hb.IMD"))
        self.label_14.setText(_translate("chargeViewer", "Precharge.pack_charge_status.charge_enable"))
        self.label_11.setText(_translate("chargeViewer", "Precharge.pack_charge_status.power"))
        self.label_15.setText(_translate("chargeViewer", "Precharge.pack_charge_status.voltage"))
        self.label_16.setText(_translate("chargeViewer", "Precharge.pack_charge_status.current"))
        self.groupBox_5.setTitle(_translate("chargeViewer", "Orion Status"))
        self.label_20.setText(_translate("chargeViewer", "OrionBMS.orion_info.dtc_status"))
        self.label_23.setText(_translate("chargeViewer", "OrionBMS.orion_currents_volts.pack_voltage"))
        self.label_24.setText(_translate("chargeViewer", "OrionBMS.orion_currents_volts.pack_current"))
        self.label_12.setText(_translate("chargeViewer", "OrionBMS.orion_info.pack_dcl"))
        self.label_21.setText(_translate("chargeViewer", "OrionBMS.orion_info.pack_ccl"))
        self.label_22.setText(_translate("chargeViewer", "OrionBMS.orion_info.pack_soc"))
        self.groupBox_6.setTitle(_translate("chargeViewer", "Elcon Status"))
        self.label_25.setText(_translate("chargeViewer", "Charger.elcon_charger_status.charge_voltage"))
        self.label_26.setText(_translate("chargeViewer", "Charger.elcon_charger_status.charge_current"))
        self.label_27.setText(_translate("chargeViewer", "Charger.elcon_charger_status.startup_fail"))
        self.label_13.setText(_translate("chargeViewer", "Charger.elcon_charger_status.hw_fail"))
        self.label_28.setText(_translate("chargeViewer", "Charger.elcon_charger_status.temp_fail"))
        self.label_29.setText(_translate("chargeViewer", "Charger.elcon_charger_status.input_v_fail"))
        self.groupBox_7.setTitle(_translate("chargeViewer", "TMU"))
        self.label_32.setText(_translate("chargeViewer", "Precharge.max_cell_temp.max_temp"))
        self.label_33.setText(_translate("chargeViewer", "Precharge.mod_cell_temp_max.temp_A"))
        self.label_34.setText(_translate("chargeViewer", "Precharge.mod_cell_temp_max.temp_B"))
        self.label_35.setText(_translate("chargeViewer", "Precharge.mod_cell_temp_max.temp_C"))
        self.label_36.setText(_translate("chargeViewer", "Precharge.mod_cell_temp_max.temp_D"))
from display_widgets.variables.can_variable_display import CANVariableDisplay
from display_widgets.variables.daq_variable_display import DAQVariableDisplay
