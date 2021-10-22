# -*- coding: utf-8 -*-
from __future__ import print_function

import weakref

from acq4.devices.DAQGeneric import DAQGeneric
from acq4.util.DaqChannelGui import DaqMultiChannelTaskGuis
from acq4.devices.Device import TaskGui
from acq4.util import Qt
from pyqtgraph.WidgetGroup import WidgetGroup


class DAQGenericTaskGui(TaskGui):
    def __init__(self, dev: DAQGeneric, task, ownUi=True):
        TaskGui.__init__(self, dev, task)
        self.uiMaker = DaqMultiChannelTaskGuis(dev.name())
        if ownUi:
            self.layout = Qt.QGridLayout()
            self.setLayout(self.layout)
            self.layout.addWidget(self.uiMaker.asWidget(), 0, 0)
            self.createChannelWidgets(self.controlSplitter, self.plotSplitter)
            self.stateGroup = WidgetGroup([
                (self.ui.topSplitter, 'splitter1'),
                (self.ui.controlSplitter, 'splitter2'),
                (self.ui.plotSplitter, 'splitter3'),
            ])
        else:
            self.stateGroup = None

        # Make sure task interface includes our DAQ device
        firstChanName = list(self.dev._DGConfig.keys())[0]
        self.daqDev = self.dev.getDAQName(firstChanName)
        self.daqUI = self.taskRunner().getDevice(self.daqDev)

        # update whenever the daq state has changed (sample rate, n samples)
        self.daqChanged(self.daqUI.currentState())
        self.daqUI.sigChanged.connect(self.daqChanged)

        # update when holding value has changed on device
        self.dev.sigHoldingChanged.connect(self.updateHolding)

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

    def daqChanged(self, state):
        pass

    def updateHolding(self):
        hv = self.getHoldingValue()
        if hv is not None:
            if not self.ui.holdingCheck.isChecked():
                self.ui.holdingSpin.setValue(hv)
            self.ui.waveGeneratorWidget.setOffset(hv)

    def getHoldingValue(self):
        """Return the value for this channel that will be used when the task is run
        (by default, this is just the current holding value)"""
        if self.ui.holdingCheck.isChecked():
            return self.ui.holdingSpin.value()
        else:
            return self.taskGui().getChanHolding(self.name)

    def saveState(self):
        if self.stateGroup is not None:
            state = self.stateGroup.state().copy()
        else:
            state = {}
        state['channels'] = {}
        for ch in self.channels:
            state['channels'][ch] = self.channels[ch].saveState()
        return state

    def restoreState(self, state):
        try:
            if self.stateGroup is not None:
                self.stateGroup.setState(state)
            for ch in state['channels']:
                try:
                    self.channels[ch].restoreState(state['channels'][ch])
                except KeyError:
                    printExc("Warning: Cannot restore state for channel %s.%s (channel does not exist on this device)" % (self.dev.name(), ch))
                    continue
        except:
            printExc('Error while restoring GUI state:')

"""
TODO:



- call updateHolding when needed


"""