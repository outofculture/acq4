# -*- coding: utf-8 -*-
from __future__ import print_function

from acq4.devices.Device import Device, TaskGui
from acq4.util import Qt
from acq4.util.DaqChannelGui import DaqMultiChannelTaskGuis
from pyqtgraph import ComboBox


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

    def listModes(self):
        """Return a dict describing clamp modes available.

        Format is::

            {
                'IC':  {'primaryUnits': 'A', 'secondaryUnits': 'V', 'commandAllowed': True},
                'I=0': {'primaryUnits': 'A', 'secondaryUnits': 'V', 'commandAllowed': False},
                'VC':  {'primaryUnits': 'V', 'secondaryUnits': 'A', 'commandAllowed': True},
            }
        """
        raise NotImplementedError()

    def getMode(self):
        """Get the currently active clamp mode ('IC', 'VC', etc.)
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


class ClampTaskCtrlWidget(Qt.QWidget):
    """Widget for configuring clamp-device-specific parameters in task ui.

    PatchClamp subclasses may extend/replace this class to customize.
    """
    def __init__(self, parent):
        Qt.QWidget.__init__(self, parent)
        self.layout = Qt.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)

        self.clampModeCombo = ComboBox(items=list(self.parent().dev.listModes().keys()))


class ClampTaskGui(TaskGui):
    def __init__(self, dev, taskRunner):
        super(ClampTaskGui, self).__init__(dev, taskRunner)
        self._numPts = None
        self._uiMaker = DaqMultiChannelTaskGuis(dev.name())
        self.sigSequenceChanged.connect(self._uiMaker.sigSequenceChanged)
        self._layout = Qt.QGridLayout()
        self.setLayout(self._layout)
        self._layout.addWidget(self._uiMaker.asWidget(), 0, 0)
        self._controlsUi = self.initControlUi()
        # calculated attrs
        self._uiMaker.addControlWidget(self._controlsUi)
        self._outputWidget, _ = self._uiMaker.createChannelWidget("command", "ao", "V")
        self._inputWidget, _ = self._uiMaker.createChannelWidget("primary", "ai", "A")

        self.daqConfigChanged()
        self.clampModeChanged()

    def initControlUi(self):
        """TODO"""
        ui = ClampTaskCtrlWidget(self)
        ui.clampModeCombo.currentIndexChanged.connect(self.clampModeChanged)
        return ui

    def listSequence(self):
        return self._uiMaker.listSequence()

    def taskSequenceStarted(self):
        return self._uiMaker.taskSequenceStarted()

    def taskStarted(self, params):
        return self._uiMaker.taskStarted(params)

    def quit(self):
        return self._uiMaker.quit()

    def saveState(self):
        return self._uiMaker.saveState()

    def restoreState(self, state):
        self._uiMaker.restoreState(state)
        self.daqConfigChanged()
        self.clampModeChanged()

    def generateTask(self, params=None):
        cmd = self._uiMaker.generateTask(params)
        cmd.update({
            "daqConfig": self.getDAQConfig(),
            "mode": self.getClampMode(),
        })
        return cmd

    def getDAQConfig(self) -> dict:
        """Return a dict describing the DAQ configuration that will be used in this task.

        Minimally includes the keys 'rate' and 'numPts'.
        """
        raise NotImplementedError()

    def clampModeChanged(self):
        # TODO handle other modes
        if self.getClampMode() == "VC":
            self._outputWidget.setUnits("V")
            self._inputWidget.setUnits("A")
        else:  # IC
            self._outputWidget.setUnits("A")
            self._inputWidget.setUnits("V")

    def getClampMode(self):
        return self._controlsUi.clampModeCombo.currentText()

    def daqConfigChanged(self):
        daqConfig = self.getDAQConfig()
        self._outputWidget.daqStateChanged(daqConfig)
        self._inputWidget.daqStateChanged(daqConfig)

    def handleResult(self, result, params):
        return self._uiMaker.handleResult(result, params)
