from acq4.devices.PatchClamp.patchclamp import ClampTaskGui, ClampTaskCtrlWidget
from acq4.util import Qt
from pyqtgraph import siFormat
from sensapex.uma import UMA

extraTaskControlsTemplate = Qt.importTemplate(".extraTaskControls")


class SensapexTaskCtrlWidget(ClampTaskCtrlWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ourWidget = Qt.QWidget()
        self.ui = extraTaskControlsTemplate()
        self.ui.setupUi(ourWidget)
        self.layout.addWidget(ourWidget, self.layout.rowCount(), 0, 1, 2)
        self.ui.sampleRateCombo.setItems({str(r): r for r in UMA.VALID_SAMPLE_RATES})
        self.ui.sampleRateCombo.setValue(parent.dev.getSampleRate())


class SensapexClampTaskGui(ClampTaskGui):
    _ctrlWidgetClass = SensapexTaskCtrlWidget

    def __init__(self, dev, taskRunner):
        super().__init__(dev, taskRunner)
        taskRunner.sigTaskChanged.connect(self.taskRunnerChanged)
        self.daqConfigChanged()

    def initControlUi(self):
        ui = SensapexTaskCtrlWidget(self)
        ui.ui.sampleRateCombo.currentIndexChanged.connect(self.daqConfigChanged)
        ui.ui.clampModeCombo.currentIndexChanged.connect(self.clampModeChanged)
        return ui

    def taskRunnerChanged(self, name, value):
        if name == "duration":
            self.daqConfigChanged()

    def generateTask(self, params=None):
        cmd = super().generateTask(params)
        cmd["DAQConfig"] = self.getDAQConfig()
        return cmd

    def getDAQConfig(self):
        rate = float(self._controlsUi.ui.sampleRateCombo.value())
        taskDuration = self.taskRunner.getParam("duration")
        return {"rate": rate, "numPts": int(taskDuration * rate)}

    def getClampMode(self):
        return self._controlsUi.ui.clampModeCombo.currentText()

    def daqConfigChanged(self):
        super().daqConfigChanged()
        daqConfig = self.getDAQConfig()
        self._controlsUi.ui.samplePeriodLabel.setText(siFormat(1.0 / daqConfig['rate'], suffix="s"))
        self._controlsUi.ui.numPointsLabel.setText(str(daqConfig['numPts']))


class SensapexClampDeviceGui(Qt.QWidget):
    def __init__(self, dev, window):
        super().__init__()
        self._dev = dev
        # TODO
