from acq4.devices.Device import TaskGui
from acq4.util import Qt
from acq4.util.DaqChannelGui import DaqMultiChannelTaskGuis
from pyqtgraph import siFormat
from sensapex.uma import UMA

extraTaskControlsTemplate = Qt.importTemplate(".extraTaskControls")


class SensapexClampTaskGui(TaskGui):
    def __init__(self, dev, taskRunner):
        super(SensapexClampTaskGui, self).__init__(dev, taskRunner)
        self._numPts = None
        uiMaker = DaqMultiChannelTaskGuis(dev.name())
        self._layout = Qt.QGridLayout()
        self.setLayout(self._layout)
        self._layout.addWidget(uiMaker.asWidget(), 0, 0)
        self.controls = Qt.QWidget()
        self.controlsUi = extraTaskControlsTemplate()
        self.controlsUi.setupUi(self.controls)
        self.controlsUi.sampleRateCombo.setItems({str(r): r for r in UMA.VALID_SAMPLE_RATES})
        self.controlsUi.sampleRateCombo.setValue(dev.getSampleRate())
        self.controlsUi.sampleRateCombo.currentIndexChanged.connect(self.updateDaqParameters)
        self.controlsUi.clampModeCombo.currentIndexChanged.connect(self.clampModeChanged)
        self.taskRunner.sigTaskChanged.connect(self.taskRunnerChanged)
        # calculated attrs
        uiMaker.addControlWidget(self.controls)
        self._outputWidget, _ = uiMaker.createChannelWidget("command", "ao", "V")
        self._inputWidget, _ = uiMaker.createChannelWidget("primary", "ai", "A")

        self.updateDaqParameters()
        self.clampModeChanged()

    def taskRunnerChanged(self, n, v):
        if n == "duration":
            self.updateDaqParameters()

    def clampModeChanged(self):
        if self.controlsUi.clampModeCombo.currentText() == "VC":
            self._outputWidget.setUnits("A")
            self._inputWidget.setUnits("V")
        else:  # IC
            self._outputWidget.setUnits("V")
            self._inputWidget.setUnits("A")

    def updateDaqParameters(self):
        rate = self.controlsUi.sampleRateCombo.value()
        taskDuration = self.taskRunner.getParam("duration")
        self._numPts = int(taskDuration * rate)
        self.controlsUi.samplePeriodLabel.setText(siFormat(1.0 / rate, suffix="s"))  #
        self.controlsUi.numPointsLabel.setText(str(self._numPts))
        self._outputWidget.daqStateChanged({"rate": rate, "numPts": self._numPts})
        self._inputWidget.daqStateChanged({"rate": rate, "numPts": self._numPts})

    def whatInterfaceDoesThisObjectNeed(self):
        self.fail()  # TODO createTask?


class SensapexClampDeviceGui(Qt.QWidget):
    def __init__(self, dev, window):
        super(SensapexClampDeviceGui, self).__init__()
        self._dev = dev
        # TODO
