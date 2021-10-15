# -*- coding: utf-8 -*-
from __future__ import print_function

from acq4.devices.DAQGeneric import DAQGenericTaskGui
from acq4.devices.Device import Device, TaskGui
from acq4.util import Qt
from pyqtgraph import WidgetGroup


class PatchClamp(Device):
    """Base class for all patch clamp amplifier devices.
    
    Signals
    -------
    sigStateChanged(state)
        Emitted when any state parameters have changed
    sigHoldingChanged(self, clamp_mode)
        Emitted when the holding value for any clamp mode has changed
    """

    sigStateChanged = Qt.Signal(object)  # state
    sigHoldingChanged = Qt.Signal(object, object)  # self, mode

    def __init__(self, deviceManager, config, name):
        Device.__init__(self, deviceManager, config, name)

    def getState(self):
        """Return a dictionary of active state parameters
        """
        raise NotImplementedError()

    def getParam(self, param):
        """Return the value of a single state parameter
        """
        raise NotImplementedError()

    def setParam(self, param, value):
        """Set the value of a single state parameter
        """
        raise NotImplementedError()

    def getHolding(self, mode=None):
        """Return the holding value for a specific clamp mode.
        
        If no clamp mode is given, then return the holding value for the currently active clamp mode.
        """
        raise NotImplementedError()

    def setHolding(self, mode=None, value=None):
        """Set the holding value for a specific clamp mode.
        """
        raise NotImplementedError()

    def autoPipetteOffset(self):
        """Automatically set the pipette offset.
        """
        raise NotImplementedError()

    def autoBridgeBalance(self):
        """Automatically set the bridge balance.
        """
        raise NotImplementedError()

    def autoCapComp(self):
        """Automatically configure capacitance compensation.
        """
        raise NotImplementedError()

    def getMode(self):
        """Get the currently active clamp mode ('IC', 'VC', etc.)
        """
        raise NotImplementedError()

    def getDaqGenericDevice(self):
        """
        Returns the DAQGeneric device that can be used to access this clamp's signal and trigger channels.
        """
        raise NotImplementedError()

    def setMode(self, mode):
        """Set the currently active clamp mode ('IC', 'VC', etc.)
        """
        raise NotImplementedError()

    def getDAQName(self, channel):
        """Return the name of the DAQ device that performs digitization for this amplifier channel.
        """
        raise NotImplementedError()

    def taskInterface(self, taskRunner):
        return ClampTaskGui(self, taskRunner)


class ClampTaskGui(TaskGui):
    def __init__(self, dev: PatchClamp, taskRunner):
        super(ClampTaskGui, self).__init__(dev, taskRunner)
        self.clampDev = dev

        self.layout = Qt.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.splitter1 = Qt.QSplitter()
        self.splitter1.setOrientation(Qt.Qt.Horizontal)
        self.layout.addWidget(self.splitter1)

        self.splitter2 = Qt.QSplitter()
        self.splitter2.setOrientation(Qt.Qt.Vertical)
        self.modeCombo = Qt.QComboBox()
        self.splitter2.addWidget(self.modeCombo)
        self.modeCombo.addItems(self.clampDev.listModes())

        self.splitter3 = Qt.QSplitter()
        self.splitter3.setOrientation(Qt.Qt.Vertical)

        (w1, p1) = self.createChannelWidget('primary')
        (w2, p2) = self.createChannelWidget('command')

        self.cmdWidget = w2
        self.inputWidget = w1
        self.cmdPlot = p2
        self.inputPlot = p1
        self.cmdWidget.setMeta('x', siPrefix=True, suffix='s', dec=True)
        self.cmdWidget.setMeta('y', siPrefix=True, dec=True)

        self.splitter1.addWidget(self.splitter2)
        self.splitter1.addWidget(self.splitter3)
        self.splitter2.addWidget(w1)
        self.splitter2.addWidget(w2)
        self.splitter3.addWidget(p1)
        self.splitter3.addWidget(p2)
        self.splitter1.setSizes([100, 500])

        self.stateGroup = WidgetGroup([
            (self.splitter1, 'splitter1'),
            (self.splitter2, 'splitter2'),
            (self.splitter3, 'splitter3'),
        ])

        self.modeCombo.currentIndexChanged.connect(self.modeChanged)
        self.modeChanged()

    def saveState(self):
        """Return a dictionary representing the current state of the widget."""
        state = {}
        state['daqState'] = DAQGenericTaskGui.saveState(self)
        state['mode'] = self.getMode()
        # state['holdingEnabled'] = self.ctrl.holdingCheck.isChecked()
        # state['holding'] = self.ctrl.holdingSpin.value()
        return state

    def restoreState(self, state):
        """Restore the state of the widget from a dictionary previously generated using saveState"""
        # print 'state: ', state
        # print 'DaqGeneric : ', dir(DAQGenericTaskGui)
        if 'mode' in state:
            self.modeCombo.setCurrentIndex(self.modeCombo.findText(state['mode']))
        # self.ctrl.holdingCheck.setChecked(state['holdingEnabled'])
        # if state['holdingEnabled']:
        #    self.ctrl.holdingSpin.setValue(state['holding'])
        if 'daqState' in state:
            return DAQGenericTaskGui.restoreState(self, state['daqState'])
        else:
            return None

    def generateTask(self, params=None):
        daqTask = DAQGenericTaskGui.generateTask(self, params)

        task = {
            'mode': self.getMode(),
            'daqProtocol': daqTask
        }

        return task

    def modeChanged(self):
        global ivModes
        ivm = ivModes[self.getMode()]
        w = self.cmdWidget

        if ivm == 'VC':
            scale = 1e-3
            cmdUnits = 'V'
            inpUnits = 'A'
        else:
            scale = 1e-12
            cmdUnits = 'A'
            inpUnits = 'V'

        self.inputWidget.setUnits(inpUnits)
        self.cmdWidget.setUnits(cmdUnits)
        self.cmdWidget.setMeta('y', minStep=scale, step=scale * 10, value=0.)
        self.inputPlot.setLabel('left', units=inpUnits)
        self.cmdPlot.setLabel('left', units=cmdUnits)
        # w.setScale(scale)
        # for s in w.getSpins():
        # s.setOpts(minStep=scale)

        self.cmdWidget.updateHolding()

    def getMode(self):
        return str(self.modeCombo.currentText())

    def sequenceChanged(self):
        self.sigSequenceChanged.emit(self.clampDev.name())

    def getChanHolding(self, chan):
        if chan == 'command':
            return self.clampDev.getHolding(self.getMode())
        else:
            raise Exception("Can't get holding value for channel %s" % chan)