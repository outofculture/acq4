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
                'IC':  {'type': 'IC', 'commandAllowed': True},
                'I=0': {'type': 'IC', 'commandAllowed': False},
                'VC':  {'type': 'VC', 'commandAllowed': True},
            }
        """
        raise NotImplementedError()

    def getChannelUnits(self, chan):
        """Return the units (usually either 'V' or 'A') used by a channel.

        *chan* may be 'command', 'primary', or 'secondary'.
        """
        modeInfo = self.listModes()[self.getMode()]
        iv = modeInfo['type']
        if iv == 'VC':
            units = ['V', 'A']
        else:
            units = ['A', 'V']

        if chan == 'command':
            return units[0]
        elif chan == 'secondary':
            return units[0]
        elif chan == 'primary':
            return units[1]

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




class ClampTaskGui(TaskGui):
    def __init__(self, dev, taskRunner):
        super(ClampTaskGui, self).__init__(dev, taskRunner)
        self._uiMaker = DaqMultiChannelTaskGuis(dev.name())
        self.sigSequenceChanged.connect(self._uiMaker.sigSequenceChanged)

        self.layout = Qt.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.layout.addWidget(self._uiMaker.asWidget(), 0, 0)

        self.ctrlWidget = Qt.QWidget(self)
        self.ctrlLayout = Qt.QGridLayout()
        self.ctrlWidget.setLayout(self.layout)
        self.ctrlLayout.setContentsMargins(0, 0, 0, 0)
        self.ctrlLayout.setSpacing(3)

        self.initControlUi(self.ctrlLayout)
        self._uiMaker.addControlWidget(self.ctrlWidget)

        self.commandWidget, _ = self._uiMaker.createChannelWidget("command", "ao", "V")
        self.primaryWidget, _ = self._uiMaker.createChannelWidget("primary", "ai", "A")
        self.secondaryWidget, _ = self._uiMaker.createChannelWidget("secondary", "ai", "V")

        self.daqConfigChanged()
        self.clampModeChanged()

    def initControlUi(self, layout):
        """Generate widgets for specifying the PatchClamp device configuration
        to use during the task.

        All widgets should be added to *layout*.

        The default implementation simply creates a combo box for selecting the clamp mode.
        """
        self.clampModeLabel = Qt.QLabel('clamp mode')
        self.clampModeCombo = ComboBox(items=list(self.dev.listModes().keys()))
        self.clampModeCombo.setObjectName("clampMode")
        self.clampModeCombo.currentIndexChanged.connect(self.clampModeChanged)
        layout.addWidget(self.clampModeLabel, 0, 0)
        layout.addWidget(self.clampModeCombo, 0, 1)

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
            self.commandWidget.setUnits("V")
            self.primaryWidget.setUnits("A")
        else:  # IC
            self.commandWidget.setUnits("A")
            self.primaryWidget.setUnits("V")

    def getClampMode(self):
        return self._controlsUi.clampModeCombo.currentText()

    def daqConfigChanged(self):
        daqConfig = self.getDAQConfig()
        self.commandWidget.daqStateChanged(daqConfig)
        self.primaryWidget.daqStateChanged(daqConfig)

    def handleResult(self, result, params):
        return self._uiMaker.handleResult(result, params)
