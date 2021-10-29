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
        self._uiMaker = DaqMultiChannelTaskGuis(dev.name())
        self.sigSequenceChanged.connect(self._uiMaker.sigSequenceChanged)
        self._layout = Qt.QGridLayout()
        self.setLayout(self._layout)
        self._layout.addWidget(self._uiMaker.asWidget(), 0, 0)
        self.controls = Qt.QWidget()
        self.controlsUi = extraTaskControlsTemplate()
        self.controlsUi.setupUi(self.controls)
        self.controlsUi.sampleRateCombo.setItems({str(r): r for r in UMA.VALID_SAMPLE_RATES})
        self.controlsUi.sampleRateCombo.setValue(dev.getSampleRate())
        self.controlsUi.sampleRateCombo.currentIndexChanged.connect(self.updateDaqParameters)
        self.controlsUi.clampModeCombo.currentIndexChanged.connect(self.clampModeChanged)
        self.taskRunner.sigTaskChanged.connect(self.taskRunnerChanged)
        # calculated attrs
        self._uiMaker.addControlWidget(self.controls)
        self._outputWidget, _ = self._uiMaker.createChannelWidget("command", "ao", "V")
        self._inputWidget, _ = self._uiMaker.createChannelWidget("primary", "ai", "A")

        self.updateDaqParameters()
        self.clampModeChanged()

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
        return self._uiMaker.restoreState(state)

    def generateTask(self, params=None):
        self.updateDaqParameters()
        outputTask = self._outputWidget.generateTask()
        # TODO what is preset?
        return {
            "command": outputTask.get("command"),
            "sampleRate": self.getSampleRate(),
            "mode": self.controlsUi.clampModeCombo.currentText(),
            "holding": outputTask.get("holding"),
            "numPts": self._numPts,
        }

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
        rate = self.getSampleRate()
        taskDuration = self.taskRunner.getParam("duration")
        self._numPts = int(taskDuration * rate)
        self.controlsUi.samplePeriodLabel.setText(siFormat(1.0 / rate, suffix="s"))  #
        self.controlsUi.numPointsLabel.setText(str(self._numPts))
        self._outputWidget.daqStateChanged({"rate": rate, "numPts": self._numPts})
        self._inputWidget.daqStateChanged({"rate": rate, "numPts": self._numPts})

    def handleResult(self, result, params):
        return self._uiMaker.handleResult(result, params)

    def getSampleRate(self):
        return self.controlsUi.sampleRateCombo.value()


class SensapexClampDeviceGui(Qt.QWidget):
    def __init__(self, dev, window):
        super(SensapexClampDeviceGui, self).__init__()
        self._dev = dev
        # TODO
