import numpy as np

from acq4.devices.Device import DeviceTask
from acq4.devices.PatchClamp import PatchClamp
from acq4.devices.SensapexClamp.guis import SensapexClampTaskGui, SensapexClampDeviceGui
from acq4.util import ptime
from pyqtgraph import MetaArray
from pyqtgraph.metaarray import axis
from sensapex.uma import UMA

__all__ = ["SensapexClamp", "SensapexClampTask"]


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
    def __init__(self, dev: SensapexClamp, cmd: dict, parentTask):
        required_keys = {"numPts", "mode", "sampleRate"}
        if not required_keys.issubset(cmd.keys()):
            raise ValueError(f"Task specification missing {required_keys - cmd.keys()}")
        super().__init__(dev, cmd, parentTask)
        self.dev = dev
        self._umaDev = dev._dev
        self._cmd = cmd
        self._numPoints = cmd["numPts"]
        self._startTime = None
        self.state = None
        self._internalStartTime = None
        self._timestampBufferIndex = 0
        self._primaryBufferIndex = 0
        self._secondaryBufferIndex = 0
        self._timestampDataBuffer = None
        self._primaryDataBuffer = None
        self._secondaryDataBuffer = None

    def start(self):
        self._startTime = ptime.time()
        self._umaDev.start_receiving()

    def isDone(self):
        return self._timestampBufferIndex >= self._numPoints

    def configure(self):
        self._umaDev.stop_receiving()
        if self._cmd.get("command", None) is not None:
            self._umaDev.send_stimulus_scaled(self._cmd["command"])
        self._timestampBufferIndex = 0
        self._primaryBufferIndex = 0
        self._secondaryBufferIndex = 0
        # TODO honor save-data checkbox
        self._timestampDataBuffer = np.zeros(shape=(self._numPoints,), dtype=float)
        self._primaryDataBuffer = np.zeros(shape=(self._numPoints,), dtype=float)
        self._secondaryDataBuffer = np.zeros(shape=(self._numPoints,), dtype=float)
        self._umaDev.add_receive_data_handler_scaled(self._receiveTimestamps, column="ts")
        self._umaDev.add_receive_data_handler_scaled(
            self._receivePrimaryData, column="current" if self._cmd["mode"] == "VC" else "voltage"
        )
        self._umaDev.add_receive_data_handler_scaled(
            self._receiveSecondaryData, column="voltage" if self._cmd["mode"] == "VC" else "current"
        )
        self.dev.setMode(self._cmd["mode"])
        if self._cmd.get("holding", None) is not None:
            self.dev.setHolding(self._cmd["holding"])
        self._umaDev.set_sample_rate(self._cmd["sampleRate"])
        self.state = self.dev.getState()

    def _receiveTimestamps(self, data):
        if self._internalStartTime is None:
            self._internalStartTime = data[0]
        start = self._timestampBufferIndex
        self._timestampBufferIndex = end = self._calculateEndIndex(start, data)
        self._timestampDataBuffer[start:end] = data[0:end - start] - self._internalStartTime

    def _calculateEndIndex(self, start, data):
        end = start + data.shape[0]
        return min(end, self._numPoints)

    def _receivePrimaryData(self, data):
        start = self._primaryBufferIndex
        self._primaryBufferIndex = end = self._calculateEndIndex(start, data)
        self._primaryDataBuffer[start:end] = data[0:end - start]

    def _receiveSecondaryData(self, data):
        start = self._secondaryBufferIndex
        self._secondaryBufferIndex = end = self._calculateEndIndex(start, data)
        self._secondaryDataBuffer[start:end] = data[0:end - start]

    def getResult(self):
        result = {
            "command": self.getCommandDataForResult(),
            "primary": self.getPrimaryDataForResult(),
            "secondary": self.getSecondaryDataForResult(),
        }

        channelList = [np.atleast_2d(result[ch]["data"]) for ch in result if result[ch]["data"] is not None]
        arr = np.concatenate(channelList)

        taskInfo = self._cmd.copy()
        if "command" in taskInfo:
            del taskInfo["command"]
        info = [
            axis(name="Channel", cols=[(ch, result[ch]["units"]) for ch in result if result[ch]["data"] is not None]),
            axis(name="Time", units="s", values=self._timestampDataBuffer),
            {
                "ClampState": self.state,
                "DAQ": {ch: result[ch]["info"] for ch in result},
                "Protocol": taskInfo,
                "startTime": self._startTime,
            },
        ]

        return MetaArray(arr, info=info)

    def stop(self, abort=False):
        # TODO stop device (restore to previous running-ness?)
        # TODO reset holding value
        primary = "current" if self._cmd["mode"] == "VC" else "voltage"
        self._umaDev.remove_receive_data_handler(self._receivePrimaryData, primary)
        secondary = "current" if self._cmd["mode"] == "VC" else "voltage"
        self._umaDev.remove_receive_data_handler(self._receiveSecondaryData, secondary)
        self._umaDev.remove_receive_data_handler(self._receiveTimestamps, "ts")

    def getPrimaryDataForResult(self):
        return {
            "info": {},  # TODO
            "data": self._primaryDataBuffer,
            "units": "A" if self._cmd["mode"] == "VC" else "V",
            "name": "primary",
        }

    def getCommandDataForResult(self):
        return {
            "data": self._cmd.get("command", None),
            "holding": self._cmd.get("holding", None),
            "info": {},  # TODO
            "name": "command",
            "units": "V" if self._cmd["mode"] == "VC" else "A",
        }

    def getSecondaryDataForResult(self):
        return {
            "info": {},  # TODO
            "data": self._secondaryDataBuffer,
            "units": "V" if self._cmd["mode"] == "VC" else "A",
            "name": "secondary",
        }
