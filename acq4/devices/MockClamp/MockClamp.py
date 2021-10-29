#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, with_statement

import os

import pyqtgraph.multiprocess as mp
from acq4 import getManager
from acq4.devices.AxoPatch200 import CancelException
from acq4.devices.DAQGeneric import DAQGenericTask
from acq4.devices.PatchClamp import PatchClamp
from acq4.devices.PatchClamp.patchclamp import ClampTaskGui
from acq4.util import Qt
from acq4.util.Mutex import Mutex
from acq4.util.debug import printExc

Ui_MockClampDevGui = Qt.importTemplate('.devTemplate')

modes = {
    'IC': {'type': 'IC', 'commandAllowed': True},
    'I=0': {'type': 'IC', 'commandAllowed': False},
    'VC': {'type': 'VC', 'commandAllowed': True},
}


class MockClamp(PatchClamp):

    def __init__(self, dm, config, name):

        PatchClamp.__init__(self, dm, config, name)

        # Generate config to use for DAQ 
        self.devLock = Mutex(Mutex.Recursive)

        self.daqConfig = {
            'command': config['Command'],
            'primary': config['ScaledSignal'],
        }

        self.holding = {
            'VC': config.get('vcHolding', -0.05),
            'IC': config.get('icHolding', 0.0)
        }

        self.mode = 'I=0'

        self.config = config

        # create a daq device under the hood
        self.daqDev = getManager().loadDevice("DAQGeneric", self.daqConfig, '{}Daq'.format(name))

        try:
            self.setHolding()
        except:
            printExc("Error while setting holding value:")

        # Start a remote process to run the simulation.
        self.process = mp.Process()
        rsys = self.process._import('sys')
        rsys._setProxyOptions(returnType='proxy')  # need to access remote path by proxy, not by value
        rsys.path.append(os.path.abspath(os.path.dirname(__file__)))
        if config['simulator'] == 'builtin':
            self.simulator = self.process._import('hhSim')
        elif config['simulator'] == 'neuron':
            self.simulator = self.process._import('neuronSim')

        dm.declareInterface(name, ['clamp'], self)

    def createTask(self, cmd, parentTask):
        return MockClampTask(self, cmd, parentTask)

    def taskInterface(self, taskRunner):
        return MockClampTaskGui(self, taskRunner)

    def deviceInterface(self, win):
        return MockClampDevGui(self)

    def setHolding(self, mode=None, value=None, force=False):
        with self.devLock:
            currentMode = self.getMode()
            if mode is None:
                mode = currentMode
            ivMode = self.listModes()[mode]['type']  ## determine vc/ic

            if value is None:
                value = self.holding[ivMode]
            else:
                self.holding[ivMode] = value

            self.sigHoldingChanged.emit('primary', self.holding.copy())

    def setChanHolding(self, chan, value=None):
        if chan == 'command':
            self.setHolding(value=value)
        else:
            self.daqDev.setChanHolding(self, chan, value)

    def getChanHolding(self, chan: str):
        if chan == 'command':
            return self.getHolding()
        else:
            return self.daqDev.getChanHolding(chan)

    def getHolding(self, mode) -> float:
        with self.devLock:
            if mode is None:
                mode = self.getMode()
            ivMode = self.listModes()[mode]['type']  # determine vc/ic
            return self.holding[ivMode]

    def getState(self) -> dict:
        return {
            'mode': self.getMode(),
        }

    def listModes(self) -> dict:
        global modes
        return modes

    def setMode(self, mode: str):
        """Set the mode of the AxoPatch (by requesting user intervention). Takes care of switching holding levels in I=0 mode if needed."""
        mode = mode.upper()
        startMode = self.getMode()
        if startMode == mode:
            return

        modes = self.listModes()
        startIvMode = modes[startMode]['type']
        ivMode = modes[mode]['type']
        if (startIvMode == 'VC' and ivMode == 'IC') or (startIvMode == 'IC' and ivMode == 'VC'):
            ## switch to I=0 first
            # self.requestModeSwitch('I=0')
            self.mode = 'I=0'

        self.setHolding(ivMode, force=True)  ## we're in I=0 mode now, so it's ok to force the holding value.

        ### TODO:
        ### If mode switches back the wrong direction, we need to reset the holding value and cancel.
        self.mode = ivMode
        self.sigStateChanged.emit(self.getState())

    def getMode(self):
        return self.mode

    def readChannel(self, ch):
        pass

    def quit(self):
        # self.process.send(None)
        self.process.close()
        self.daqDev.quit()

    def getDAQName(self, channel):
        """Return the DAQ name used by this device. (assumes there is only one DAQ for now)"""
        return self.daqConfig[channel]['device']

    def autoPipetteOffset(self):
        """Automatically set the pipette offset.
        """
        pass

    def autoBridgeBalance(self):
        """Automatically set the bridge balance.
        """
        pass

    def autoCapComp(self):
        """Automatically configure capacitance compensation.
        """
        pass


class MockClampTask(DAQGenericTask):
    def __init__(self, dev, cmd, parentTask):
        ## make a few changes for compatibility with multiclamp        
        if 'daqProtocol' not in cmd:
            cmd['daqProtocol'] = {}

        daqP = cmd['daqProtocol']

        if 'command' in cmd:
            if 'holding' in cmd:
                daqP['command'] = {'command': cmd['command'], 'holding': cmd['holding']}
            else:
                daqP['command'] = {'command': cmd['command']}
        daqP['command']['lowLevelConf'] = {'mockFunc': self.write}

        cmd['daqProtocol']['primary'] = {'record': True, 'lowLevelConf': {'mockFunc': self.read}}
        DAQGenericTask.__init__(self, dev.daqDev, cmd['daqProtocol'], parentTask)

        self.cmd = cmd
        self.clampDev = dev

        modPath = os.path.abspath(os.path.split(__file__)[0])

    def configure(self):
        ### Record initial state or set initial value
        ##if 'holding' in self.cmd:
        ##    self.dev.setHolding(self.cmd['mode'], self.cmd['holding'])
        if 'mode' in self.cmd:
            self.clampDev.setMode(self.cmd['mode'])
        mode = self.clampDev.getMode()
        self.ampState = {
            'mode': mode,
            'primaryUnits': 'A' if mode == 'VC' else 'V',
            # copying multiclamp format here, but should eventually pick something more universal 
            'ClampParams': ({
                                'BridgeBalResist': 0,
                                'BridgeBalEnable': True,
                            } if mode == 'IC' else {}),
        }

        ### Do not configure daq until mode is set. Otherwise, holding values may be incorrect.
        DAQGenericTask.configure(self)

    def read(self):
        ## Called by DAQGeneric to simulate a read-from-DAQ
        res = self.job.result(timeout=30)._getValue()
        return res

    def write(self, data, dt):
        ## Called by DAQGeneric to simulate a write-to-DAQ
        self.job = self.clampDev.simulator.run({'data': data, 'dt': dt, 'mode': self.cmd['mode']}, _callSync='async')

    def isDone(self):
        ## check on neuron process
        # return self.process.poll() is not None
        return True

    def stop(self, abort=False):
        DAQGenericTask.stop(self, abort)

    def getResult(self):
        result = DAQGenericTask.getResult(self)
        result._info[-1]['startTime'] = next(iter(result._info[-1][self.clampDev.getDAQName("primary")].values()))['startTime']
        result._info[-1]['ClampState'] = self.ampState
        return result


class MockClampTaskGui(ClampTaskGui):
    def getDAQConfig(self):
        daqName = self.dev.getDAQName('primary')
        daqUI = self.taskRunner.getDevice(daqName)
        return daqUI.currentState()


class MockClampDevGui(Qt.QWidget):
    def __init__(self, dev):
        Qt.QWidget.__init__(self)
        self.dev = dev
        self.ui = Ui_MockClampDevGui()
        self.ui.setupUi(self)
        self.ui.vcHoldingSpin.setOpts(step=1, minStep=1e-3, dec=True, suffix='V', siPrefix=True)
        self.ui.icHoldingSpin.setOpts(step=1, minStep=1e-12, dec=True, suffix='A', siPrefix=True)
        # self.ui.modeCombo.currentIndexChanged.connect(self.modeComboChanged)
        self.modeRadios = {
            'VC': self.ui.vcModeRadio,
            'IC': self.ui.icModeRadio,
            'I=0': self.ui.i0ModeRadio,
        }
        self.updateStatus()

        for v in self.modeRadios.values():
            v.toggled.connect(self.modeRadioChanged)
        self.ui.vcHoldingSpin.valueChanged.connect(self.vcHoldingChanged)
        self.ui.icHoldingSpin.valueChanged.connect(self.icHoldingChanged)
        self.dev.sigHoldingChanged.connect(self.devHoldingChanged)
        self.dev.sigStateChanged.connect(self.devStateChanged)

    def updateStatus(self):
        global modeNames
        mode = self.dev.getMode()
        if mode is None:
            return
        vcHold = self.dev.getHolding('VC')
        icHold = self.dev.getHolding('IC')
        self.modeRadios[mode].setChecked(True)
        # self.ui.modeCombo.setCurrentIndex(self.ui.modeCombo.findText(mode))
        self.ui.vcHoldingSpin.setValue(vcHold)
        self.ui.icHoldingSpin.setValue(icHold)

    def devHoldingChanged(self, chan, hval):
        if isinstance(hval, dict):
            self.ui.vcHoldingSpin.blockSignals(True)
            self.ui.icHoldingSpin.blockSignals(True)
            self.ui.vcHoldingSpin.setValue(hval['VC'])
            self.ui.icHoldingSpin.setValue(hval['IC'])
            self.ui.vcHoldingSpin.blockSignals(False)
            self.ui.icHoldingSpin.blockSignals(False)

    def devStateChanged(self):
        mode = self.dev.getMode()
        for r in self.modeRadios.values():
            r.blockSignals(True)
        # self.ui.modeCombo.blockSignals(True)
        # self.ui.modeCombo.setCurrentIndex(self.ui.modeCombo.findText(mode))
        self.modeRadios[mode].setChecked(True)
        # self.ui.modeCombo.blockSignals(False)
        for r in self.modeRadios.values():
            r.blockSignals(False)

    def vcHoldingChanged(self):
        self.dev.setHolding('VC', self.ui.vcHoldingSpin.value())

    def icHoldingChanged(self):
        self.dev.setHolding('IC', self.ui.icHoldingSpin.value())

    def modeRadioChanged(self, m):
        try:
            if not m:
                return
            for mode, r in self.modeRadios.items():
                if r.isChecked():
                    self.dev.setMode(mode)
        except CancelException:
            self.updateStatus()
