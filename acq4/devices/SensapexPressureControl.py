from __future__ import print_function

from threading import Thread
from time import sleep

from acq4.drivers.sensapex import UMP
from acq4.util import Qt
from .PressureControl import PressureControl, PressureControlWidget


class SensapexPressureControl(PressureControl):
    """Pressure control device driven by Sensapex analog/digital channels.
    """
    sigMeasuredPressureChanged = Qt.Signal(object, object)  # self, pressure

    def __init__(self, manager, config, name):
        self.devId = config.get('deviceId')
        if manager.config.get("drivers", {}).get("sensapex", {}).get("driverPath", None) is not None:
            UMP.set_library_path(manager.config["drivers"]["sensapex"]["driverPath"])
        address = config.pop('address', None)
        group = config.pop('group', None)
        ump = UMP.get_ump(address=address, group=group)
        self.dev = ump.get_device(self.devId)
        config.setdefault("maximum", 7e4)
        config.setdefault("minimum", -7e4)
        PressureControl.__init__(self, manager, config, name)

        self.pressureChannel = config.pop('pressureChannel')
        self._valveValueBySource = {"regulator": 1, "atmosphere": 0}
        self.sources = tuple(self._valveValueBySource.keys())
        self._busy = self.dev.is_busy()
        self._measurement = self.dev.measure_pressure(self.pressureChannel)
        self.source = self.getSource()
        self.pressure = self.getPressure()
        self._pollThread = Thread(target=self._poll)
        self._pollThread.daemon = True
        self._pollThread.start()

    def _poll(self):
        while True:
            self.getBusyStatus()
            self.measurePressure()
            sleep(self.regulatorSettlingTime)

    def _setPressure(self, p):
        self.dev.set_pressure(self.pressureChannel, p / 1000.)

    def getPressure(self):
        return self.dev.get_pressure(self.pressureChannel) * 1000

    def measurePressure(self):
        pressure = self.dev.measure_pressure(self.pressureChannel)
        if pressure != self._measurement:
            self._measurement = pressure
            self.sigMeasuredPressureChanged.emit(self, pressure)
        return pressure

    def getSource(self):
        if self.dev.get_valve(self.pressureChannel) == 1:
            return "regulator"
        else:
            return "atmosphere"

    def _setSource(self, source):
        self.dev.set_valve(self.pressureChannel, self._valveValueBySource[source])

    def calibrate(self):
        self.dev.calibrate_pressure(self.pressureChannel)

    def getBusyStatus(self):
        busy = self.dev.is_busy()
        if busy != self._busy:
            self._busy = busy
            self.sigBusyChanged.emit(self, busy)
        return busy

    def deviceInterface(self, win):
        return SensapexPressureControlWidget(dev=self)


class SensapexPressureControlWidget(Qt.QWidget):
    """Supports measured pressure display and calibration"""

    def __init__(self, dev):
        super(SensapexPressureControlWidget, self).__init__()
        self.dev = dev
        self.layout = Qt.QGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.calibrateButton = Qt.QPushButton("Calibrate")
        self.calibrateButton.clicked.connect(self.dev.calibrate)
        self.layout.addWidget(self.calibrateButton, 0, 0)

        self.controlWidget = PressureControlWidget(self, dev)
        self.layout.addWidget(self.controlWidget, 0, 1)

        self.measurement = Qt.QLineEdit()
        self.measurement.setPlaceholderText("-")
        self.measurement.setReadOnly(True)
        self.measurement.setTextMargins(20, 4, 20, 4)
        self.layout.addWidget(self.measurement, 0, 2)
        self._measurementChanged(dev, dev.measurePressure())
        dev.sigMeasuredPressureChanged.connect(self._measurementChanged)

        self._busyChanged(dev, dev.getBusyStatus())
        dev.sigBusyChanged.connect(self._busyChanged)

    def _measurementChanged(self, dev, pressure):
        self.measurement.setText(f"{pressure:+.04f} kPa")

    def _busyChanged(self, dev, isBusy):
        self.calibrateButton.setEnabled(not isBusy)
