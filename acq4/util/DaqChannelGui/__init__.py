# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy
from six.moves import range

from acq4.devices.Device import TaskGui
from acq4.util import Qt
from acq4.util.SequenceRunner import runSequence
from acq4.util.debug import printExc
from pyqtgraph import SpinBox, WidgetGroup, mkPen, PlotWidget

AOChannelTemplate = Qt.importTemplate(".AOChannelTemplate")
DOChannelTemplate = Qt.importTemplate(".DOChannelTemplate")
InputChannelTemplate = Qt.importTemplate(".InputChannelTemplate")


class DaqMultiChannelTaskGuis(Qt.QObject):
    """
    Encapsulates standard user interfaces and logic around handling analog input/output signals in TaskRunner.

    - Input channels have a control panel with "record" and "display" check boxes
    - Input channels have a plot widget that displays incoming data, potentially overlapping plots if they came
      from the same sequence
    - Output channels have a function generator and plot widget
    - Output plots include the single and sequence commands, the most recently executed command
    - Includes logic for saving/restoring ui state, generating task commands

    Usage::

         guis = DaqMultiChannelTaskGuis()
         for chan in channels:
             ctrlwidget, plotwidget = guis.createChannelWidget(chan.name, chan.chanType, chan.units)
             # put the widgets in your gui

         - OR -

         guis = DaqMultiChannelTaskGuis()
         for chan in channels:
             guis.createChannelWidget(chan.name, chan.chanType, chan.units)
         widget = guis.asWidget()  # embed all created widgets in splitters and return top-level splitter
         # put a default widget in your UI; includes splitters
    """

    sigSequenceChanged = Qt.Signal(object)

    def __init__(self, deviceName):
        super().__init__()
        self.deviceName = deviceName
        self._widgetsByChannel = {}
        self._plotsByChannel = {}
        self.stateGroup = WidgetGroup([])
        self.topSplitter = None

    def asWidget(self) -> Qt.QWidget:
        if self.topSplitter is None:
            self.topSplitter = Qt.QSplitter(Qt.Qt.Horizontal)
            self.controlSplitter = Qt.QSplitter(Qt.Qt.Vertical)
            self.plotSplitter = Qt.QSplitter(Qt.Qt.Vertical)
            self.topSplitter.addWidget(self.controlSplitter)
            self.topSplitter.addWidget(self.plotSplitter)
            self.stateGroup.addWidget(self.topSplitter, "splitter1")
            self.stateGroup.addWidget(self.controlSplitter, "splitter2")
            self.stateGroup.addWidget(self.plotSplitter, "splitter3")
            self.topSplitter.setStretchFactor(0, 0)
            self.topSplitter.setStretchFactor(1, 1)

            for widget in self._widgetsByChannel.values():
                self.controlSplitter.addWidget(widget)
            for widget in self._plotsByChannel.values():
                self.plotSplitter.addWidget(widget)

        return self.topSplitter

    def createChannelWidget(self, channelName, chanType, units, parent=None):
        if chanType in ["ao", "do"]:
            w = OutputChannelGui(
                groupName=self.deviceName, channelName=channelName, units=units, channelType=chanType, parent=parent
            )
            w.sigSequenceChanged.connect(self.sequenceChanged)
        elif chanType in ["ai", "di"]:
            w = InputChannelGui(
                groupName=self.deviceName, channelName=channelName, units=units, channelType=chanType, parent=parent
            )
        else:
            raise ValueError(f"Unrecognized device type '{chanType}'")
        self._widgetsByChannel[channelName] = w
        self._plotsByChannel[channelName] = w.plot
        if self.topSplitter is not None:
            self.controlSplitter.addWidget(w)
            self.plotSplitter.addWidget(w.plot)
        return w, w.plot

    def daqStateChanged(self, state):
        for widget in self._widgetsByChannel.values():
            widget.daqStateChanged(state)

    def saveState(self):
        if self.stateGroup is not None:
            state = self.stateGroup.state().copy()
        else:
            state = {}
        state["channels"] = {}
        for ch in self._widgetsByChannel:
            state["channels"][ch] = self._widgetsByChannel[ch].saveState()
        return state

    def restoreState(self, state):
        try:
            if self.stateGroup is not None:
                self.stateGroup.setState(state)
            for ch in state["channels"]:
                try:
                    self._widgetsByChannel[ch].restoreState(state["channels"][ch])
                except KeyError:
                    printExc(
                        f"Warning: Cannot restore state for channel {self.deviceName}.{ch} (channel does not exist on this device)"
                    )
                    continue
        except:
            printExc("Error while restoring GUI state:")

    def listSequence(self):
        # returns sequence parameter names and lengths
        l = {}
        for ch in self._widgetsByChannel:
            chl = self._widgetsByChannel[ch].listSequence()
            for k in chl:
                l[ch + "." + k] = chl[k]
        return l

    def sequenceChanged(self):
        self.sigSequenceChanged.emit(self.deviceName)

    def taskStarted(self, params):  # automatically invoked from TaskGui
        # Pull out parameters for this device
        params = dict([(p[1], params[p]) for p in params if p[0] == self.deviceName])

        for ch in self._widgetsByChannel:
            search = ch + "."
            # Extract just the parameters the channel will need
            chParams = {k[len(search) :]: params[k] for k in params if k[: len(search)] == search}

            self._widgetsByChannel[ch].taskStarted(chParams)

    def taskSequenceStarted(self):  # automatically invoked from TaskGui
        for ch in self._widgetsByChannel:
            self._widgetsByChannel[ch].taskSequenceStarted()

    def generateTask(self, params=None):
        if params is None:
            params = {}
        p = {}
        for ch in self._widgetsByChannel:
            search = ch + "."
            # Extract just the parameters the channel will need
            chParams = {k[len(search) :]: params[k] for k in params if k[: len(search)] == search}

            # request the task from the channel
            p[ch] = self._widgetsByChannel[ch].generateTask(chParams)
        return p

    def handleResult(self, result, params):
        if result is None:
            return
        for ch in self._widgetsByChannel:
            if result.hasColumn(0, ch):
                self._widgetsByChannel[ch].handleResult(result[ch], params)

    def quit(self):
        TaskGui.quit(self)
        for ch in self._widgetsByChannel:
            self._widgetsByChannel[ch].quit()


class DaqChannelGui(Qt.QWidget):
    def __init__(self, groupName, channelName, units, channelType, parent=None):
        Qt.QWidget.__init__(self, parent)
        self.units = units
        self.channelName = channelName
        self.channelType = channelType
        self.deviceHoldingValue = None
        self.rate = 1
        self.numPts = 0
        self.timeVals = []

        # if plot is not None:
        # plot widget
        self.plot = PlotWidget(parent=parent)
        self.plot.setLabel("left", text=channelName, units=self.units)
        self.plot.registerPlot(groupName + "." + channelName)
        self.plot.setDownsampling(ds=True, auto=True, mode="peak")
        self.plot.setClipToView(True)

        self.scale = 1.0

    def postUiInit(self):
        # Automatically locate all read/writable widgets and group them together for easy
        # save/restore operations
        self.stateGroup = WidgetGroup(self)
        self.stateGroup.addWidget(self.plot, name="plot")

        self.displayCheckChanged()
        self.ui.displayCheck.stateChanged.connect(self.displayCheckChanged)

        self.setUnits(self.units)

    def updateTitle(self):
        self.ui.groupBox.setTitle(f"{self.channelName} ({self.units})")

    def setUnits(self, units):
        self.units = units
        for s in self.getSpins():
            if isinstance(s, SpinBox):
                s.setOpts(suffix=units)
        self.updateTitle()

    def getSpins(self):
        return []

    def setChildrenVisible(self, obj, vis):
        for c in obj.children():
            if isinstance(c, Qt.QWidget):
                c.setVisible(vis)
            else:
                self.setChildrenVisible(c, vis)

    def daqStateChanged(self, state):
        pass  # subclasses can override

    def saveState(self):
        return self.stateGroup.state()

    def restoreState(self, state):
        self.stateGroup.setState(state)
        if hasattr(self.ui, "waveGeneratorWidget"):
            self.ui.waveGeneratorWidget.update()

    def clearPlots(self):
        self.plot.clear()
        self.currentPlot = None

    def displayCheckChanged(self):
        if self.stateGroup.state()["displayCheck"]:
            self.plot.show()
        else:
            self.plot.hide()

    def taskStarted(self, params):
        pass

    def taskSequenceStarted(self):
        pass

    def quit(self):
        self.plot.close()


class OutputChannelGui(DaqChannelGui):
    sigSequenceChanged = Qt.Signal(object)
    sigDataChanged = Qt.Signal(object)

    def __init__(self, groupName, channelName, units, channelType, parent=None):
        self._block_update = False  # blocks plotting during state changes
        DaqChannelGui.__init__(self, groupName, channelName, units, channelType, parent=parent)

        self.plot.setLabel("left", text=channelName, units=self.units)
        self.plot.registerPlot(groupName + "." + channelName)

        self.units = ""  # TODO ?
        self.currentPlot = None
        if self.channelType == "ao":
            self.ui = AOChannelTemplate()
        elif self.channelType == "do":
            self.ui = DOChannelTemplate()
        else:
            raise Exception(f"Unrecognized channel type '{self.channelType}'")
        self.ui.setupUi(self)
        self.postUiInit()

        if self.channelType == "ao":
            for s in self.getSpins():
                s.setOpts(dec=True, bounds=[None, None], step=1.0, minStep=1e-12, siPrefix=True)

        self.ui.waveGeneratorWidget.sigDataChanged.connect(self.updateWaves)
        self.ui.waveGeneratorWidget.sigFunctionChanged.connect(self.waveFunctionChanged)
        self.ui.waveGeneratorWidget.sigParametersChanged.connect(self.sequenceChanged)
        self.ui.holdingCheck.stateChanged.connect(self.holdingCheckChanged)
        self.ui.holdingSpin.valueChanged.connect(self.holdingSpinChanged)
        self.ui.functionCheck.toggled.connect(self.functionCheckToggled)

        self.holdingCheckChanged()
        self.ui.functionCheck.setChecked(True)

    def getSpins(self):
        return self.ui.preSetSpin, self.ui.holdingSpin

    def setMeta(self, key, **kwargs):
        # key is 'x' (time), 'y' (amp), or 'xy' (sum)
        self.ui.waveGeneratorWidget.setMeta(key, **kwargs)

    def setUnits(self, units, **kwargs):
        DaqChannelGui.setUnits(self, units)
        self.ui.waveGeneratorWidget.setMeta("y", units=units, siPrefix=True, **kwargs)

    def quit(self):
        DaqChannelGui.quit(self)

        self.ui.waveGeneratorWidget.sigDataChanged.disconnect(self.updateWaves)
        self.ui.waveGeneratorWidget.sigFunctionChanged.disconnect(self.waveFunctionChanged)
        self.ui.waveGeneratorWidget.sigParametersChanged.disconnect(self.sequenceChanged)
        self.ui.holdingCheck.stateChanged.disconnect(self.holdingCheckChanged)
        self.ui.holdingSpin.valueChanged.disconnect(self.holdingSpinChanged)

    def functionCheckToggled(self, checked):
        if checked:
            self.ui.waveGeneratorWidget.setEnabled(True)
        else:
            self.ui.waveGeneratorWidget.setEnabled(False)
        self.updateWaves()

    def daqStateChanged(self, state):
        self.rate = state["rate"]
        self.numPts = state["numPts"]
        self.timeVals = numpy.linspace(0, float(self.numPts) / self.rate, self.numPts)
        self.updateWaves()

    def listSequence(self):
        return self.ui.waveGeneratorWidget.listSequences()

    def sequenceChanged(self):
        self.sigSequenceChanged.emit(self.channelName)

    def generateTask(self, params=None):
        if params is None:
            params = {}
        prot = {}
        state = self.stateGroup.state()
        if state["preSetCheck"]:
            prot["preset"] = state["preSetSpin"]
        if state["holdingCheck"]:
            prot["holding"] = state["holdingSpin"]
        if state["functionCheck"]:
            prot["command"] = self.getSingleWave(params)

        return prot

    def handleResult(self, result, params):
        pass

    def updateWaves(self):
        if self._block_update:
            return
        if not self.ui.functionCheck.isChecked():
            self.plot.clear()
            return

        self.clearPlots()

        ps = self.ui.waveGeneratorWidget.listSequences()
        # display sequence waves
        params = {k: list(range(len(ps[k]))) for k in ps}
        waves = []
        runSequence(
            lambda p: waves.append(self.getSingleWave(p)), params, list(params.keys())
        )  # appends waveforms for the entire parameter space to waves

        autoRange = self.plot.getViewBox().autoRangeEnabled()
        self.plot.enableAutoRange(x=False, y=False)
        try:
            for w in waves:
                if w is not None:
                    # self.ui.functionCheck.setChecked(True)
                    self.plotCurve(w, color=Qt.QColor(100, 100, 100))

            # display single-mode wave in red
            single = self.getSingleWave()
            if single is not None:
                # self.ui.functionCheck.setChecked(True)
                self.plotCurve(single, color=Qt.QColor(200, 100, 100))
        finally:
            self.plot.enableAutoRange(x=autoRange[0], y=autoRange[1])

        self.sigDataChanged.emit(self)

    def taskStarted(self, params):
        # Draw green trace for current command waveform
        if not self.stateGroup.state()["displayCheck"]:
            return
        if self.currentPlot is not None:
            self.plot.removeItem(self.currentPlot)

        cur = self.getSingleWave(params)
        if cur is not None:
            self.currentPlot = self.plotCurve(cur, color=Qt.QColor(100, 200, 100))
            self.currentPlot.setZValue(100)

    def plotCurve(self, data, color=Qt.QColor(100, 100, 100), replot=True):
        return self.plot.plot(y=data, x=self.timeVals, pen=mkPen(color))

    def getSingleWave(self, params=None):
        state = self.stateGroup.state()
        h = self.getHoldingValue()
        if h is not None:
            self.ui.waveGeneratorWidget.setOffset(h)

        return self.ui.waveGeneratorWidget.getSingle(self.rate, self.numPts, params)

    def holdingCheckChanged(self, *v):
        self.ui.holdingSpin.setEnabled(self.ui.holdingCheck.isChecked())
        self.updateHolding()

    def holdingSpinChanged(self, *args):
        hv = self.getHoldingValue()
        if hv is not None:
            self.ui.waveGeneratorWidget.setOffset(hv)

    def deviceHoldingValueChanged(self, holdingValue):
        self.deviceHoldingValue = holdingValue
        self.updateHolding()

    def updateHolding(self):
        if self.ui.holdingCheck.isChecked():
            hv = self.ui.holdingSpin.value()
        else:
            hv = self.deviceHoldingValue
            if hv is not None:
                self.ui.holdingSpin.setValue(hv)
        if hv is not None:
            self.ui.waveGeneratorWidget.setOffset(hv)

    def getHoldingValue(self):
        """Return the value for this channel that will be used when the task is run
        (by default, this is just the current holding value)"""
        if self.ui.holdingCheck.isChecked():
            return self.ui.holdingSpin.value()
        else:
            return self.deviceHoldingValue

    def waveFunctionChanged(self):
        if self.ui.waveGeneratorWidget.functionString() != "":
            self.ui.functionCheck.setChecked(True)
        else:
            self.ui.functionCheck.setChecked(False)

    def restoreState(self, state):
        block = self._block_update
        self._block_update = True
        try:
            DaqChannelGui.restoreState(self, state)
        finally:
            self._block_update = False

        self.updateWaves()


class InputChannelGui(DaqChannelGui):
    def __init__(self, groupName, channelName, units, channelType, parent=None):
        DaqChannelGui.__init__(self, groupName, channelName, units, channelType, parent=parent)
        self.ui = InputChannelTemplate()
        self.ui.setupUi(self)
        self.postUiInit()
        self.clearBeforeNextPlot = False

    def taskSequenceStarted(self):
        self.clearBeforeNextPlot = True

    def listSequence(self):
        return []

    def generateTask(self, params=None):
        state = self.stateGroup.state()
        return {"record": state["recordCheck"], "recordInit": state["recordInitCheck"]}

    def handleResult(self, result, params):
        if self.stateGroup.state()["displayCheck"]:
            if self.clearBeforeNextPlot:
                self.clearPlots()
                self.clearBeforeNextPlot = False

            plot = self.plot.plot(
                y=result.view(numpy.ndarray), x=result.xvals("Time"), pen=mkPen(200, 200, 200), params=params
            )
