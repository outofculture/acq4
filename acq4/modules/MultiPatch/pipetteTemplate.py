# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pipetteTemplate.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_PipetteControl(object):
    def setupUi(self, PipetteControl):
        PipetteControl.setObjectName(_fromUtf8("PipetteControl"))
        PipetteControl.resize(1004, 122)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PipetteControl.sizePolicy().hasHeightForWidth())
        PipetteControl.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(PipetteControl)
        self.gridLayout.setMargin(0)
        self.gridLayout.setHorizontalSpacing(2)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_5 = QtGui.QLabel(PipetteControl)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.label_6 = QtGui.QLabel(PipetteControl)
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 0, 1, 1, 1)
        self.label = QtGui.QLabel(PipetteControl)
        self.label.setMaximumSize(QtCore.QSize(65, 16777215))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 2, 1, 1)
        self.label_2 = QtGui.QLabel(PipetteControl)
        self.label_2.setMaximumSize(QtCore.QSize(65, 16777215))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 3, 1, 1)
        self.label_3 = QtGui.QLabel(PipetteControl)
        self.label_3.setMaximumSize(QtCore.QSize(65, 16777215))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 4, 1, 1)
        self.label_4 = QtGui.QLabel(PipetteControl)
        self.label_4.setMaximumSize(QtCore.QSize(65, 16777215))
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 0, 5, 1, 1)
        self.activeBtn = QtGui.QPushButton(PipetteControl)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.activeBtn.sizePolicy().hasHeightForWidth())
        self.activeBtn.setSizePolicy(sizePolicy)
        self.activeBtn.setMinimumSize(QtCore.QSize(30, 0))
        self.activeBtn.setMaximumSize(QtCore.QSize(30, 16777215))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.activeBtn.setFont(font)
        self.activeBtn.setCheckable(True)
        self.activeBtn.setObjectName(_fromUtf8("activeBtn"))
        self.gridLayout.addWidget(self.activeBtn, 1, 0, 1, 1)
        self.selectBtn = QtGui.QPushButton(PipetteControl)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectBtn.sizePolicy().hasHeightForWidth())
        self.selectBtn.setSizePolicy(sizePolicy)
        self.selectBtn.setMinimumSize(QtCore.QSize(30, 0))
        self.selectBtn.setMaximumSize(QtCore.QSize(30, 16777215))
        self.selectBtn.setCheckable(True)
        self.selectBtn.setObjectName(_fromUtf8("selectBtn"))
        self.gridLayout.addWidget(self.selectBtn, 1, 1, 1, 1)
        self.widget = QtGui.QWidget(PipetteControl)
        self.widget.setMaximumSize(QtCore.QSize(65, 16777215))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.stateText = QtGui.QLineEdit(self.widget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.stateText.setFont(font)
        self.stateText.setAlignment(QtCore.Qt.AlignCenter)
        self.stateText.setReadOnly(True)
        self.stateText.setObjectName(_fromUtf8("stateText"))
        self.verticalLayout.addWidget(self.stateText)
        self.lockBtn = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lockBtn.sizePolicy().hasHeightForWidth())
        self.lockBtn.setSizePolicy(sizePolicy)
        self.lockBtn.setCheckable(True)
        self.lockBtn.setObjectName(_fromUtf8("lockBtn"))
        self.verticalLayout.addWidget(self.lockBtn)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.targetBtn = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.targetBtn.sizePolicy().hasHeightForWidth())
        self.targetBtn.setSizePolicy(sizePolicy)
        self.targetBtn.setObjectName(_fromUtf8("targetBtn"))
        self.horizontalLayout.addWidget(self.targetBtn)
        self.tipBtn = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tipBtn.sizePolicy().hasHeightForWidth())
        self.tipBtn.setSizePolicy(sizePolicy)
        self.tipBtn.setObjectName(_fromUtf8("tipBtn"))
        self.horizontalLayout.addWidget(self.tipBtn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addWidget(self.widget, 1, 2, 1, 1)
        self.widget_2 = QtGui.QWidget(PipetteControl)
        self.widget_2.setMaximumSize(QtCore.QSize(65, 16777215))
        self.widget_2.setObjectName(_fromUtf8("widget_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.widget_2)
        self.verticalLayout_2.setMargin(2)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.modeText = QtGui.QLineEdit(self.widget_2)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.modeText.setFont(font)
        self.modeText.setAlignment(QtCore.Qt.AlignCenter)
        self.modeText.setReadOnly(True)
        self.modeText.setObjectName(_fromUtf8("modeText"))
        self.verticalLayout_2.addWidget(self.modeText)
        self.autoOffsetBtn = QtGui.QPushButton(self.widget_2)
        self.autoOffsetBtn.setObjectName(_fromUtf8("autoOffsetBtn"))
        self.verticalLayout_2.addWidget(self.autoOffsetBtn)
        self.autoPipCapBtn = QtGui.QPushButton(self.widget_2)
        self.autoPipCapBtn.setObjectName(_fromUtf8("autoPipCapBtn"))
        self.verticalLayout_2.addWidget(self.autoPipCapBtn)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.gridLayout.addWidget(self.widget_2, 1, 3, 1, 1)
        self.widget_3 = QtGui.QWidget(PipetteControl)
        self.widget_3.setMinimumSize(QtCore.QSize(0, 0))
        self.widget_3.setMaximumSize(QtCore.QSize(65, 16777215))
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.widget_3)
        self.verticalLayout_3.setMargin(2)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.holdingSpin = QtGui.QDoubleSpinBox(self.widget_3)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.holdingSpin.setFont(font)
        self.holdingSpin.setAlignment(QtCore.Qt.AlignCenter)
        self.holdingSpin.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.holdingSpin.setObjectName(_fromUtf8("holdingSpin"))
        self.verticalLayout_3.addWidget(self.holdingSpin)
        self.autoBiasBtn = QtGui.QPushButton(self.widget_3)
        self.autoBiasBtn.setCheckable(True)
        self.autoBiasBtn.setObjectName(_fromUtf8("autoBiasBtn"))
        self.verticalLayout_3.addWidget(self.autoBiasBtn)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem2)
        self.gridLayout.addWidget(self.widget_3, 1, 4, 1, 1)
        self.widget_4 = QtGui.QWidget(PipetteControl)
        self.widget_4.setMaximumSize(QtCore.QSize(65, 16777215))
        self.widget_4.setObjectName(_fromUtf8("widget_4"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.widget_4)
        self.verticalLayout_4.setMargin(2)
        self.verticalLayout_4.setSpacing(2)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.pressureSpin = QtGui.QDoubleSpinBox(self.widget_4)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pressureSpin.setFont(font)
        self.pressureSpin.setAlignment(QtCore.Qt.AlignCenter)
        self.pressureSpin.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.pressureSpin.setObjectName(_fromUtf8("pressureSpin"))
        self.verticalLayout_4.addWidget(self.pressureSpin)
        self.autoPressureBtn = QtGui.QPushButton(self.widget_4)
        self.autoPressureBtn.setCheckable(True)
        self.autoPressureBtn.setObjectName(_fromUtf8("autoPressureBtn"))
        self.verticalLayout_4.addWidget(self.autoPressureBtn)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.userPressureBtn = QtGui.QPushButton(self.widget_4)
        self.userPressureBtn.setCheckable(True)
        self.userPressureBtn.setObjectName(_fromUtf8("userPressureBtn"))
        self.horizontalLayout_3.addWidget(self.userPressureBtn)
        self.atmPressureBtn = QtGui.QPushButton(self.widget_4)
        self.atmPressureBtn.setCheckable(True)
        self.atmPressureBtn.setObjectName(_fromUtf8("atmPressureBtn"))
        self.horizontalLayout_3.addWidget(self.atmPressureBtn)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        spacerItem3 = QtGui.QSpacerItem(20, 22, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem3)
        self.gridLayout.addWidget(self.widget_4, 1, 5, 1, 1)
        self.plotLayoutWidget = QtGui.QWidget(PipetteControl)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotLayoutWidget.sizePolicy().hasHeightForWidth())
        self.plotLayoutWidget.setSizePolicy(sizePolicy)
        self.plotLayoutWidget.setObjectName(_fromUtf8("plotLayoutWidget"))
        self.plotLayout = QtGui.QHBoxLayout(self.plotLayoutWidget)
        self.plotLayout.setMargin(0)
        self.plotLayout.setSpacing(0)
        self.plotLayout.setObjectName(_fromUtf8("plotLayout"))
        self.gridLayout.addWidget(self.plotLayoutWidget, 1, 6, 1, 1)

        self.retranslateUi(PipetteControl)
        QtCore.QMetaObject.connectSlotsByName(PipetteControl)

    def retranslateUi(self, PipetteControl):
        PipetteControl.setWindowTitle(_translate("PipetteControl", "Form", None))
        self.label_5.setText(_translate("PipetteControl", "Enab.", None))
        self.label_6.setText(_translate("PipetteControl", "Sel.", None))
        self.label.setText(_translate("PipetteControl", "State", None))
        self.label_2.setText(_translate("PipetteControl", "Clamp Mode", None))
        self.label_3.setText(_translate("PipetteControl", "Holding", None))
        self.label_4.setText(_translate("PipetteControl", "Pres (kPa)", None))
        self.activeBtn.setText(_translate("PipetteControl", "1", None))
        self.selectBtn.setText(_translate("PipetteControl", ">", None))
        self.stateText.setText(_translate("PipetteControl", "out", None))
        self.lockBtn.setText(_translate("PipetteControl", "lock", None))
        self.targetBtn.setText(_translate("PipetteControl", "Tar", None))
        self.tipBtn.setText(_translate("PipetteControl", "Tip", None))
        self.modeText.setText(_translate("PipetteControl", "VC", None))
        self.autoOffsetBtn.setText(_translate("PipetteControl", "auto offs.", None))
        self.autoPipCapBtn.setText(_translate("PipetteControl", "pip cap", None))
        self.autoBiasBtn.setText(_translate("PipetteControl", "bias: off", None))
        self.autoPressureBtn.setText(_translate("PipetteControl", "auto", None))
        self.userPressureBtn.setText(_translate("PipetteControl", "user", None))
        self.atmPressureBtn.setText(_translate("PipetteControl", "atm", None))

