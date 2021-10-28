# -*- coding: utf-8 -*-
from __future__ import print_function

from acq4.devices.DAQGeneric import DAQGeneric
from acq4.util.DaqChannelGui import DaqMultiChannelTaskGuis
from acq4.devices.Device import TaskGui
from acq4.util import Qt
from acq4.util.debug import printExc


class DAQGenericTaskGui(TaskGui):
    def __init__(self, dev: DAQGeneric, taskRunner, ownUi=True):
        TaskGui.__init__(self, dev, taskRunner)
        self.uiMaker = DaqMultiChannelTaskGuis(dev.name())
        if ownUi:
            self.layout = Qt.QGridLayout()
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(self.layout)
            self.layout.addWidget(self.uiMaker.asWidget(), 0, 0)
            self.createChannelWidgets(self.uiMaker.controlSplitter, self.uiMaker.plotSplitter)
            self.stateGroup = self.uiMaker.stateGroup
        else:
            self.stateGroup = None

        # Make sure task interface includes our DAQ device
        firstChanName = list(self.dev._DGConfig.keys())[0]
        self.daqDev = self.dev.getDAQName(firstChanName)
        self.daqUI = self.taskRunner.getDevice(self.daqDev)

        # update whenever the daq state has changed (sample rate, n samples)
        self.daqStateChanged(self.daqUI.currentState())
        self.daqUI.sigChanged.connect(self.daqStateChanged)

        # update when holding value has changed on device
        self.dev.sigHoldingChanged.connect(self.updateHolding)

        self.uiMaker.sigSequenceChanged.connect(self.sigSequenceChanged)

    def createChannelWidgets(self, ctrlParent, plotParent):
        ## Create plots and control widgets
        for ch in self.dev._DGConfig:
            (w, p) = self.createChannelWidget(ch)
            plotParent.addWidget(p)
            ctrlParent.addWidget(w)

    def createChannelWidget(self, ch):
        units = self.dev.getChanUnits(ch)
        chanType = self.dev.getChanType(ch)
        return self.uiMaker.createChannelWidget(ch, chanType, units)

    def daqStateChanged(self, state):
        # Called when DAQ parameters have changed.
        # state is a dict containing at least 'rate' and 'numPts'
        self.uiMaker.daqStateChanged(state)

    def updateHolding(self, channel, value):
        # device changed its holding value; let the ui know so it can make any necessary updates
        ctrlWidget = self.uiMaker.getWidgets(channel)[0]
        ctrlWidget.deviceHoldingValueChanged(value)

    def saveState(self):
        return self.uiMaker.saveState()

    def restoreState(self, state):
        return self.uiMaker.restoreState(state)

    def handleResult(self, result, params):
        return self.uiMaker.handleResult(result, params)

    def listSequence(self):
        return self.uiMaker.listSequence()

    def generateTask(self, params=None):
        return self.uiMaker.generateTask(params)

    def taskSequenceStarted(self):
        return self.uiMaker.taskSequenceStarted()

    def taskStarted(self, params):
        return self.uiMaker.taskStarted(params)

