from acq4.devices.BaseDAQ import BaseDAQ
from acq4.devices.DAQGeneric import DAQGenericTaskGui, DAQGeneric
from acq4.devices.PatchClamp import PatchClamp
from acq4.util import Qt
from sensapex.uma import UMA


class QuacksLikeADAQ(BaseDAQ):
    def __init__(self, deviceManager, config, name):
        super(QuacksLikeADAQ, self).__init__(deviceManager, config, name)
        self._clamp = config["_clamp_device"]

    def createTask(self, cmd, parent_task):
        pass  # TODO


class QuacksLikeADAQGeneric(DAQGeneric):
    def __init__(self, deviceManager, config, name):
        super(QuacksLikeADAQGeneric, self).__init__(deviceManager, config, name)
        self._clamp = config["_clamp_device"]


class SensapexClamp(PatchClamp):
    def __init__(self, deviceManager, config: dict, name):
        super(SensapexClamp, self).__init__(deviceManager, config, name)
        config.setdefault("_clamp_device", self)
        self._daq_dev = deviceManager.loadDevice("SensapexClamp.QuacksLikeADAQ", config, f'{name}Daq')
        self._daq_generic_device = deviceManager.loadDevice(
            "SensapexClamp.QuacksLikeADAQGeneric", config, f'{name}DaqGeneric')
        self._manipulator = deviceManager.getDevice(config["Manipulator"])
        self._dev = UMA(self._manipulator.dev)

    def getDaqGenericDevice(self):
        return self._daq_generic_device

    def getParam(self, param):
        # TODO name mapping?
        return self._dev.get_param(param)

    def setParam(self, param, value):
        # This method is never used on clamps, so far as I can tell. MultiClamp exclusively
        # uses self.mc.setParam in all its code.
        pass

    def createTask(self, cmd, mgr_task):
        pass  # TODO

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
        return self.name

    def getState(self):
        return self._dev.get_params()

    def deviceInterface(self, win):
        return SensapexClampDeviceGui(self, win)


class SensapexClampDeviceGui(Qt.QWidget):
    def __init__(self, dev, window):
        super(SensapexClampDeviceGui, self).__init__()
        self._dev = dev
        # TODO
