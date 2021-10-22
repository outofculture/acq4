from acq4.devices.Device import DeviceTask
from acq4.devices.PatchClamp import PatchClamp
from acq4.devices.SensapexClamp.guis import SensapexClampTaskGui, SensapexClampDeviceGui
from sensapex.uma import UMA


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

    def start(self):
        self.dev.dev.start_receiving()

    def isDone(self):
        # figure out if the data has all been received
        pass

    def configure(self):
        self.dev.dev.stop_receiving()
        self.dev.dev.send_stimulus_scaled()
        # stop device
        # set mode, params
        # setup data receive hook

    def getResult(self):
        pass
