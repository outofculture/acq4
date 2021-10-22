from acq4.devices.Device import DeviceTask
from acq4.devices.PatchClamp import PatchClamp
from acq4.devices.SensapexClamp.guis import SensapexClampTaskGui, SensapexClampDeviceGui
from acq4.util import ptime
from pyqtgraph import MetaArray
from pyqtgraph.metaarray import axis
from sensapex.uma import UMA

import numpy as np


__all__ = ["SensapexClamp"]


class SensapexClamp(PatchClamp):
    def __init__(self, deviceManager, config: dict, name):
        super(SensapexClamp, self).__init__(deviceManager, config, name)
        config.setdefault("_clamp_device", self)
        self._manipulator = deviceManager.getDevice(config["Manipulator"])
        self._dev = UMA(self._manipulator.dev)

    def getParam(self, param):
        # TODO name mapping?
        return self._dev.get_param(param)

    def setParam(self, param, value):
        # This method is never used on clamps, so far as I can tell. MultiClamp exclusively
        # uses self.mc.setParam in all its code.
        pass

    def getSampleRate(self):
        return self._dev.get_param("sample_rate")

    def createTask(self, cmd, mgr_task):
        return SensapexClampTask(self, cmd, mgr_task)  # ?

    def getHolding(self, mode=None):
        if mode is None:
            mode = self.getMode()
        if mode == "VC":
            return self._dev.get_holding_current()
        else:
            return self._dev.get_holding_voltage()

    def setHolding(self, mode=None, value=None):
        if mode is None:
            mode = self.getMode()
        if mode == "VC":
            self._dev.set_holding_current(value)
        else:
            self._dev.set_holding_voltage(value)

    def autoPipetteOffset(self):
        pass  # TODO

    def autoBridgeBalance(self):
        pass  # TODO

    def autoCapComp(self):
        pass  # TODO

    def getMode(self):
        return self._dev.get_clamp_mode()

    def setMode(self, mode):
        self._dev.set_clamp_mode(mode)

    def getDAQName(self, channel):
        return None
        # TODO fix test pulse, cell-detect state, patch module, multipatch module

    def getState(self):
        return self._dev.get_params()

    def deviceInterface(self, win):
        return SensapexClampDeviceGui(self, win)

    def taskInterface(self, taskRunner):
        return SensapexClampTaskGui(self, taskRunner)


class SensapexClampTask(DeviceTask):
    def __init__(self, dev: SensapexClamp, cmd, parentTask):
        super().__init__(dev, cmd, parentTask)
        self.dev = dev
        self._cmd = cmd
        self._startTime = None
        self.state = None

    def start(self):
        self._startTime = ptime.time()
        self.dev._dev.start_receiving()

    def isDone(self):
        # TODO figure out if the data has all been received and stimulus has all been sent
        pass

    def configure(self):
        self.dev._dev.stop_receiving()
        self.dev._dev.send_stimulus_scaled(self._cmd["command"])
        self.dev._dev.add_receive_data_handler_scaled(
            self._receivePrimaryData,
            column="current" if self._cmd["mode"] == "VC" else "voltage",
        )
        self.dev._dev.add_receive_data_handler_scaled(
            self._receiveSecondaryData,
            column="voltage" if self._cmd["mode"] == "VC" else "current",
        )
        self.dev.setMode(self._cmd["mode"])
        self.dev.setHolding(self._cmd["holding"])
        self.dev._dev.set_sample_rate(self._cmd["sampleRate"])
        self.state = self.dev.getState()

    def _receivePrimaryData(self, data):
        pass

    def _receiveSecondaryData(self, data):
        pass

    def getResult(self):
        result = {"command": self.getCommandDataForResult(), "primary": self.getPrimaryDataForResult()}
        commandUnits = result["command"]["units"]
        primaryUnits = result["primary"]["units"]
        nPts = result["primary"]["info"]["numPts"]
        rate = result["primary"]["info"]["sampleRate"]

        daqState = {ch: result[ch]["info"] for ch in result}

        timeVals = np.linspace(0, float(nPts - 1) / float(rate), nPts)
        chanList = [np.atleast_2d(result[x]["data"]) for x in result]
        arr = np.concatenate(chanList)

        taskInfo = self._cmd.copy()
        if "command" in taskInfo:
            del taskInfo["command"]
        info = [
            axis(name="Channel", cols=[("command", commandUnits), ("primary", primaryUnits)]),
            axis(name="Time", units="s", values=timeVals),
            {"ClampState": self.state, "DAQ": daqState, "Protocol": taskInfo, "startTime": self._startTime},
        ]

        return MetaArray(arr, info=info)

    def stop(self, abort=False):
        # TODO stop device (restore to previous running-ness?)
        # TODO reset holding value
        column = "current" if self._cmd["mode"] == "VC" else "voltage"
        self.dev._dev.remove_receive_data_handler(self._receivePrimaryData, column)

    def getPrimaryDataForResult(self):
        data = [1]  # TODO
        return {
            "info": {},  # TODO
            "data": data,
            "units": "A" if self._cmd["mode"] == "VC" else "V",
            "name": "primary",
        }

    def getCommandDataForResult(self):
        data = self._cmd["command"]
        if data is not None:
            data *= self.state["extCmdScale"]  # TODO
        return {
            "data": data,
            "holding": self._cmd["holding"],
            "info": {},  # TODO
            "name": "command",
            "units": "V" if self._cmd["mode"] == "VC" else "A",
        }
