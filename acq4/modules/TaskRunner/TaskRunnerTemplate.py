# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'acq4/modules/TaskRunner/TaskRunnerTemplate.ui'
#
# Created: Wed Jan  8 00:49:37 2014
#      by: PyQt4 UI code generator 4.10
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1089, 309)
        MainWindow.setStyleSheet(_fromUtf8(""))
        MainWindow.setDockNestingEnabled(True)
        self.centralwidget = QtGui.QWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.LoaderDock = QtGui.QDockWidget(MainWindow)
        self.LoaderDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable|QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        self.LoaderDock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.TopDockWidgetArea)
        self.LoaderDock.setObjectName(_fromUtf8("LoaderDock"))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.LoaderDock.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(4), self.LoaderDock)
        self.TaskDock = QtGui.QDockWidget(MainWindow)
        self.TaskDock.setEnabled(True)
        self.TaskDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable|QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        self.TaskDock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.TopDockWidgetArea)
        self.TaskDock.setObjectName(_fromUtf8("TaskDock"))
        self.dockWidgetContents_5 = QtGui.QWidget()
        self.dockWidgetContents_5.setObjectName(_fromUtf8("dockWidgetContents_5"))
        self.gridLayout = QtGui.QGridLayout(self.dockWidgetContents_5)
        self.gridLayout.setMargin(0)
        self.gridLayout.setHorizontalSpacing(5)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(self.dockWidgetContents_5)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.protoContinuousCheck = QtGui.QCheckBox(self.dockWidgetContents_5)
        self.protoContinuousCheck.setEnabled(False)
        self.protoContinuousCheck.setObjectName(_fromUtf8("protoContinuousCheck"))
        self.gridLayout.addWidget(self.protoContinuousCheck, 0, 1, 1, 2)
        self.deviceList = QtGui.QListWidget(self.dockWidgetContents_5)
        self.deviceList.setObjectName(_fromUtf8("deviceList"))
        self.gridLayout.addWidget(self.deviceList, 1, 0, 5, 1)
        self.label_8 = QtGui.QLabel(self.dockWidgetContents_5)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.gridLayout.addWidget(self.label_8, 1, 1, 1, 1)
        self.label_6 = QtGui.QLabel(self.dockWidgetContents_5)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 2, 1, 1, 1)
        self.protoLoopCheck = QtGui.QCheckBox(self.dockWidgetContents_5)
        self.protoLoopCheck.setObjectName(_fromUtf8("protoLoopCheck"))
        self.gridLayout.addWidget(self.protoLoopCheck, 3, 1, 1, 1)
        self.label_7 = QtGui.QLabel(self.dockWidgetContents_5)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout.addWidget(self.label_7, 4, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 91, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 2, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.testSingleBtn = QtGui.QPushButton(self.dockWidgetContents_5)
        self.testSingleBtn.setEnabled(True)
        self.testSingleBtn.setObjectName(_fromUtf8("testSingleBtn"))
        self.horizontalLayout_2.addWidget(self.testSingleBtn)
        spacerItem1 = QtGui.QSpacerItem(13, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.runTaskBtn = QtGui.QPushButton(self.dockWidgetContents_5)
        self.runTaskBtn.setEnabled(True)
        self.runTaskBtn.setObjectName(_fromUtf8("runTaskBtn"))
        self.horizontalLayout_2.addWidget(self.runTaskBtn)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.stopSingleBtn = QtGui.QPushButton(self.dockWidgetContents_5)
        self.stopSingleBtn.setObjectName(_fromUtf8("stopSingleBtn"))
        self.horizontalLayout_2.addWidget(self.stopSingleBtn)
        self.gridLayout.addLayout(self.horizontalLayout_2, 6, 0, 1, 4)
        self.protoDurationSpin = SpinBox(self.dockWidgetContents_5)
        self.protoDurationSpin.setMinimumSize(QtCore.QSize(60, 0))
        self.protoDurationSpin.setProperty("value", 0.1)
        self.protoDurationSpin.setObjectName(_fromUtf8("protoDurationSpin"))
        self.gridLayout.addWidget(self.protoDurationSpin, 1, 2, 1, 2)
        self.protoLeadTimeSpin = SpinBox(self.dockWidgetContents_5)
        self.protoLeadTimeSpin.setProperty("value", 0.01)
        self.protoLeadTimeSpin.setObjectName(_fromUtf8("protoLeadTimeSpin"))
        self.gridLayout.addWidget(self.protoLeadTimeSpin, 2, 2, 1, 2)
        self.protoCycleTimeSpin = SpinBox(self.dockWidgetContents_5)
        self.protoCycleTimeSpin.setObjectName(_fromUtf8("protoCycleTimeSpin"))
        self.gridLayout.addWidget(self.protoCycleTimeSpin, 4, 2, 1, 2)
        self.TaskDock.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(4), self.TaskDock)
        self.SequenceDock = QtGui.QDockWidget(MainWindow)
        self.SequenceDock.setEnabled(True)
        self.SequenceDock.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable|QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        self.SequenceDock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.TopDockWidgetArea)
        self.SequenceDock.setObjectName(_fromUtf8("SequenceDock"))
        self.dockWidgetContents_7 = QtGui.QWidget()
        self.dockWidgetContents_7.setObjectName(_fromUtf8("dockWidgetContents_7"))
        self.gridLayout_2 = QtGui.QGridLayout(self.dockWidgetContents_7)
        self.gridLayout_2.setMargin(0)
        self.gridLayout_2.setHorizontalSpacing(5)
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label_10 = QtGui.QLabel(self.dockWidgetContents_7)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout_2.addWidget(self.label_10, 0, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_9 = QtGui.QLabel(self.dockWidgetContents_7)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.verticalLayout.addWidget(self.label_9)
        self.seqCycleTimeSpin = SpinBox(self.dockWidgetContents_7)
        self.seqCycleTimeSpin.setProperty("value", 1.0)
        self.seqCycleTimeSpin.setObjectName(_fromUtf8("seqCycleTimeSpin"))
        self.verticalLayout.addWidget(self.seqCycleTimeSpin)
        self.label_11 = QtGui.QLabel(self.dockWidgetContents_7)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.verticalLayout.addWidget(self.label_11)
        self.seqRepetitionSpin = QtGui.QSpinBox(self.dockWidgetContents_7)
        self.seqRepetitionSpin.setMinimum(0)
        self.seqRepetitionSpin.setMaximum(1000000)
        self.seqRepetitionSpin.setObjectName(_fromUtf8("seqRepetitionSpin"))
        self.verticalLayout.addWidget(self.seqRepetitionSpin)
        spacerItem3 = QtGui.QSpacerItem(17, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.label_2 = QtGui.QLabel(self.dockWidgetContents_7)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.paramSpaceLabel = QtGui.QLabel(self.dockWidgetContents_7)
        self.paramSpaceLabel.setObjectName(_fromUtf8("paramSpaceLabel"))
        self.verticalLayout.addWidget(self.paramSpaceLabel)
        self.label_4 = QtGui.QLabel(self.dockWidgetContents_7)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.seqTimeLabel = QtGui.QLabel(self.dockWidgetContents_7)
        self.seqTimeLabel.setObjectName(_fromUtf8("seqTimeLabel"))
        self.verticalLayout.addWidget(self.seqTimeLabel)
        self.seqCurrentLabel = QtGui.QLabel(self.dockWidgetContents_7)
        self.seqCurrentLabel.setText(_fromUtf8(""))
        self.seqCurrentLabel.setObjectName(_fromUtf8("seqCurrentLabel"))
        self.verticalLayout.addWidget(self.seqCurrentLabel)
        spacerItem4 = QtGui.QSpacerItem(13, 13, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 1, 2, 1)
        self.sequenceParamList = ParamList(self.dockWidgetContents_7)
        self.sequenceParamList.setDragEnabled(True)
        self.sequenceParamList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.sequenceParamList.setIndentation(10)
        self.sequenceParamList.setRootIsDecorated(True)
        self.sequenceParamList.setAnimated(True)
        self.sequenceParamList.setAllColumnsShowFocus(True)
        self.sequenceParamList.setObjectName(_fromUtf8("sequenceParamList"))
        self.sequenceParamList.header().setDefaultSectionSize(30)
        self.sequenceParamList.header().setMinimumSectionSize(30)
        self.sequenceParamList.header().setStretchLastSection(False)
        self.gridLayout_2.addWidget(self.sequenceParamList, 1, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.testSequenceBtn = QtGui.QPushButton(self.dockWidgetContents_7)
        self.testSequenceBtn.setEnabled(False)
        self.testSequenceBtn.setObjectName(_fromUtf8("testSequenceBtn"))
        self.horizontalLayout_3.addWidget(self.testSequenceBtn)
        spacerItem5 = QtGui.QSpacerItem(38, 17, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem5)
        self.runSequenceBtn = QtGui.QPushButton(self.dockWidgetContents_7)
        self.runSequenceBtn.setEnabled(False)
        self.runSequenceBtn.setObjectName(_fromUtf8("runSequenceBtn"))
        self.horizontalLayout_3.addWidget(self.runSequenceBtn)
        self.pauseSequenceBtn = QtGui.QPushButton(self.dockWidgetContents_7)
        self.pauseSequenceBtn.setMinimumSize(QtCore.QSize(40, 0))
        self.pauseSequenceBtn.setCheckable(True)
        self.pauseSequenceBtn.setObjectName(_fromUtf8("pauseSequenceBtn"))
        self.horizontalLayout_3.addWidget(self.pauseSequenceBtn)
        spacerItem6 = QtGui.QSpacerItem(58, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem6)
        self.stopSequenceBtn = QtGui.QPushButton(self.dockWidgetContents_7)
        self.stopSequenceBtn.setObjectName(_fromUtf8("stopSequenceBtn"))
        self.horizontalLayout_3.addWidget(self.stopSequenceBtn)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 2, 0, 1, 2)
        self.gridLayout_2.setColumnStretch(0, 5)
        self.gridLayout_2.setColumnStretch(1, 1)
        self.SequenceDock.setWidget(self.dockWidgetContents_7)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(4), self.SequenceDock)
        self.dockWidget = QtGui.QDockWidget(MainWindow)
        self.dockWidget.setFeatures(QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetMovable|QtGui.QDockWidget.DockWidgetVerticalTitleBar)
        self.dockWidget.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.TopDockWidgetArea)
        self.dockWidget.setObjectName(_fromUtf8("dockWidget"))
        self.dockWidgetContents_2 = QtGui.QWidget()
        self.dockWidgetContents_2.setObjectName(_fromUtf8("dockWidgetContents_2"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.dockWidgetContents_2)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setMargin(0)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.analysisList = QtGui.QListWidget(self.dockWidgetContents_2)
        self.analysisList.setObjectName(_fromUtf8("analysisList"))
        self.horizontalLayout_4.addWidget(self.analysisList)
        self.dockWidget.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(4), self.dockWidget)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Task Runner", None))
        self.LoaderDock.setWindowTitle(_translate("MainWindow", "Loader", None))
        self.TaskDock.setWindowTitle(_translate("MainWindow", "Task", None))
        self.label.setText(_translate("MainWindow", "Devices", None))
        self.protoContinuousCheck.setToolTip(_translate("MainWindow", "Task runs continuously without \n"
"gaps until stopped (not yet implemented).", None))
        self.protoContinuousCheck.setText(_translate("MainWindow", "Continuous", None))
        self.label_8.setText(_translate("MainWindow", "Duration", None))
        self.label_6.setText(_translate("MainWindow", "Lead Time", None))
        self.protoLoopCheck.setToolTip(_translate("MainWindow", "Task will run repeatedly until stopped and \n"
"waits a minimum of Cycle Time between episodes.\n"
"Not the same as continuous acquisition (there \n"
"will be a time gap between each recording).", None))
        self.protoLoopCheck.setText(_translate("MainWindow", "Loop", None))
        self.label_7.setText(_translate("MainWindow", "Cycle Time", None))
        self.testSingleBtn.setText(_translate("MainWindow", "Test", None))
        self.runTaskBtn.setText(_translate("MainWindow", "Record Single", None))
        self.stopSingleBtn.setText(_translate("MainWindow", "Stop Single", None))
        self.protoDurationSpin.setToolTip(_translate("MainWindow", "Duration of stimulus/acquisition in the task.", None))
        self.protoLeadTimeSpin.setToolTip(_translate("MainWindow", "Duration of time to wait before acquisition starts \n"
"(the hardware is reserved so nothing else can \n"
"run during this time).", None))
        self.protoCycleTimeSpin.setToolTip(_translate("MainWindow", "The minimum time to wait between recordings \n"
"in loop mode.", None))
        self.SequenceDock.setWindowTitle(_translate("MainWindow", "Sequence", None))
        self.label_10.setText(_translate("MainWindow", "Sequence Parameters", None))
        self.label_9.setText(_translate("MainWindow", "Cycle Time", None))
        self.label_11.setText(_translate("MainWindow", "Repetitions", None))
        self.label_2.setText(_translate("MainWindow", "Parameter Space: ", None))
        self.paramSpaceLabel.setText(_translate("MainWindow", "0", None))
        self.label_4.setText(_translate("MainWindow", "Total time:", None))
        self.seqTimeLabel.setText(_translate("MainWindow", "0", None))
        self.sequenceParamList.headerItem().setText(0, _translate("MainWindow", "dev", None))
        self.sequenceParamList.headerItem().setText(1, _translate("MainWindow", "param", None))
        self.sequenceParamList.headerItem().setText(2, _translate("MainWindow", "len", None))
        self.testSequenceBtn.setText(_translate("MainWindow", "Test", None))
        self.runSequenceBtn.setText(_translate("MainWindow", "Record Sequence", None))
        self.pauseSequenceBtn.setText(_translate("MainWindow", "Pause", None))
        self.stopSequenceBtn.setText(_translate("MainWindow", "Stop Sequence", None))
        self.dockWidget.setWindowTitle(_translate("MainWindow", "Analysis", None))

from acq4.pyqtgraph import SpinBox
from ParamList import ParamList
