# -*- coding: utf-8 -*-
from __future__ import print_function

import weakref

import numpy

from acq4.devices.Device import TaskGui
from acq4.util.debug import printExc
from pyqtgraph import SpinBox, WidgetGroup, mkPen, PlotWidget
from six.moves import range

from acq4.util import Qt
from acq4.util.SequenceRunner import runSequence

AOChannelTemplate = Qt.importTemplate('.AOChannelTemplate')
DOChannelTemplate = Qt.importTemplate('.DOChannelTemplate')
InputChannelTemplate = Qt.importTemplate('.InputChannelTemplate')


###### For task GUIs

Ui_Form = Qt.importTemplate('.TaskTemplate')


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

    def __init__(self, dev, taskRunner, ownUi=True):
        super().__init__()
        self.dev = dev
        self.taskRunner = taskRunner
        self._widgetsByChannel = {}
        self._plotsByChannel = {}
        self.stateGroup = WidgetGroup([])

        if ownUi:
            self.topSplitter = Qt.QSplitter(Qt.Qt.Horizontal)
            self.controlSplitter = Qt.QSplitter(Qt.Qt.Vertical)
            self.plotSplitter = Qt.QSplitter(Qt.Qt.Vertical)
            self.topSplitter.addWidget(self.controlSplitter)
            self.topSplitter.addWidget(self.plotSplitter)
            self.stateGroup = WidgetGroup([
                (self.topSplitter, 'splitter1'),
                (self.controlSplitter, 'splitter2'),
                (self.plotSplitter, 'splitter3'),
            ])
            self.topSplitter.setStretchFactor(0, 0)
            self.topSplitter.setStretchFactor(1, 1)

        else:
            ## If ownUi is False, then the UI is created elsewhere and createChannelWidgets must be called from there too.
            self.stateGroup = None

    def asWidget(self):
        return self.topSplitter

    def createChannelWidget(self, name, chanType, units, dev, taskRunner, daqName=None):
        if chanType in ['ao', 'do']:
            w = OutputChannelGui(self, name, chanType, units, dev, taskRunner, daqName)
            w.sigSequenceChanged.connect(self.sequenceChanged)
        elif chanType in ['ai', 'di']:
            w = InputChannelGui(self, name, chanType, units, dev, taskRunner, daqName)
        else:
            raise Exception("Unrecognized device type '%s'" % chanType)
        self._widgetsByChannel[name] = w
        self._plotsByChannel[name] = w.plot

        return w, w.plot

    def saveState(self):
        if self.stateGroup is not None:
            state = self.stateGroup.state().copy()
        else:
            state = {}
        state['channels'] = {}
        for ch in self._widgetsByChannel:
            state['channels'][ch] = self._widgetsByChannel[ch].saveState()
        return state

    def restoreState(self, state):
        try:
            if self.stateGroup is not None:
                self.stateGroup.setState(state)
            for ch in state['channels']:
                try:
                    self._widgetsByChannel[ch].restoreState(state['channels'][ch])
                except KeyError:
                    printExc(
                        "Warning: Cannot restore state for channel %s.%s (channel does not exist on this device)" % (
                        self.dev.name(), ch))
                    continue
        except:
            printExc('Error while restoring GUI state:')

    def listSequence(self):
        ## returns sequence parameter names and lengths
        l = {}
        for ch in self._widgetsByChannel:
            chl = self._widgetsByChannel[ch].listSequence()
            for k in chl:
                l[ch + '.' + k] = chl[k]
        return l

    def sequenceChanged(self):
        self.sigSequenceChanged.emit(self.dev.name())

    def taskStarted(self, params):  ## automatically invoked from TaskGui
        ## Pull out parameters for this device
        params = dict([(p[1], params[p]) for p in params if p[0] == self.dev.name()])

        for ch in self._widgetsByChannel:
            search = ch + '.'
            ## Extract just the parameters the channel will need
            chParams = {
                k[len(search) :]: params[k]
                for k in params
                if k[: len(search)] == search
            }

            self._widgetsByChannel[ch].taskStarted(chParams)

    def taskSequenceStarted(self):  ## automatically invoked from TaskGui
        for ch in self._widgetsByChannel:
            self._widgetsByChannel[ch].taskSequenceStarted()

    def generateTask(self, params=None):
        if params is None:
            params = {}
        p = {}
        for ch in self._widgetsByChannel:
            search = ch + '.'
            ## Extract just the parameters the channel will need
            chParams = {
                k[len(search) :]: params[k]
                for k in params
                if k[: len(search)] == search
            }

            ## request the task from the channel
            p[ch] = self._widgetsByChannel[ch].generateTask(chParams)
        return p

    def handleResult(self, result, params):
        if result is None:
            return
        for ch in self._widgetsByChannel:
            if result.hasColumn(0, ch):
                self._widgetsByChannel[ch].handleResult(result[ch], params)

    def getChanHolding(self, chan):
        """Return the holding value that this channel will use when the task is run."""
        return self.dev.getChanHolding(chan)

    def quit(self):
        TaskGui.quit(self)
        for ch in self._widgetsByChannel:
            self._widgetsByChannel[ch].quit()


class DaqChannelGui(Qt.QWidget):
    def __init__(self, name, chanType, units, dev, taskRunner, daqName, parent=None, plot=None):
        # self, name, units, dev, taskRunner, daqName
        Qt.QWidget.__init__(self, parent)
        self.chanType = chanType

        if plot is not None:
            plot = PlotWidget(self, parent=parent)
            plot.setLabel('left', text=name, units=units)
            plot.registerPlot(self.dev.name() + '.' + name)
        self.plot = plot


        ## Name of this channel
        self.name = name

        ## Parent taskGui object
        self.taskGui = weakref.ref(parent)

        self.scale = 1.0
        self.units = units

        ## The device handle for this channel's DAQGeneric device
        self.dev = dev

        ## The task GUI window which contains this object
        self.taskRunner = weakref.ref(taskRunner)

        ## Make sure task interface includes our DAQ device
        if daqName is None:
            self.daqDev = self.dev.getDAQName(self.name)
        else:
            self.daqDev = daqName
        self.daqUI = self.taskRunner().getDevice(self.daqDev)

        ## plot widget
        self.plot = plot
        self.plot.setDownsampling(ds=True, auto=True, mode='peak')
        self.plot.setClipToView(True)

    def postUiInit(self):
        ## Automatically locate all read/writable widgets and group them together for easy 
        ## save/restore operations
        self.stateGroup = WidgetGroup(self)
        self.stateGroup.addWidget(self.plot, name='plot')

        self.displayCheckChanged()
        self.ui.displayCheck.stateChanged.connect(self.displayCheckChanged)

        if 'units' in self.config:
            self.setUnits(self.config['units'])
        else:
            self.setUnits('')

    def updateTitle(self):
        self.ui.groupBox.setTitle(self.name + " (%s)" % self.units)

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

    def saveState(self):
        return self.stateGroup.state()

    def restoreState(self, state):
        self.stateGroup.setState(state)
        if hasattr(self.ui, 'waveGeneratorWidget'):
            self.ui.waveGeneratorWidget.update()

    def clearPlots(self):
        self.plot.clear()
        self.currentPlot = None

    def displayCheckChanged(self):
        if self.stateGroup.state()['displayCheck']:
            self.plot.show()
        else:
            self.plot.hide()

    def taskStarted(self, params):
        pass

    def taskSequenceStarted(self):
        pass

    def quit(self):
        # print "quit DAQGeneric channel", self.name
        self.plot.close()


class OutputChannelGui(DaqChannelGui):
    sigSequenceChanged = Qt.Signal(object)
    sigDataChanged = Qt.Signal(object)

    def __init__(self, parent, name, chanType, units, dev, taskRunner, daqName):
        self._block_update = False  # blocks plotting during state changes
        DaqChannelGui.__init__(self, parent, name, chanType, units, dev, taskRunner, daqName)

        self.plot.setLabel('left', text=name, units=units)
        self.plot.registerPlot(self.dev.name() + '.' + name)

        self.units = ''
        self.currentPlot = None
        if self.config['type'] == 'ao':
            self.ui = AOChannelTemplate()
        elif self.config['type'] == 'do':
            self.ui = DOChannelTemplate()
        else:
            raise Exception("Unrecognized channel type '%s'" % self.config['type'])
        self.ui.setupUi(self)
        self.postUiInit()

        self.daqChanged(self.daqUI.currentState())

        if self.config['type'] == 'ao':
            for s in self.getSpins():
                s.setOpts(dec=True, bounds=[None, None], step=1.0, minStep=1e-12, siPrefix=True)

        self.daqUI.sigChanged.connect(self.daqChanged)
        self.ui.waveGeneratorWidget.sigDataChanged.connect(self.updateWaves)
        self.ui.waveGeneratorWidget.sigFunctionChanged.connect(self.waveFunctionChanged)
        self.ui.waveGeneratorWidget.sigParametersChanged.connect(self.sequenceChanged)
        self.ui.holdingCheck.stateChanged.connect(self.holdingCheckChanged)
        self.ui.holdingSpin.valueChanged.connect(self.holdingSpinChanged)
        self.ui.functionCheck.toggled.connect(self.functionCheckToggled)
        self.dev.sigHoldingChanged.connect(self.updateHolding)

        self.holdingCheckChanged()
        self.ui.functionCheck.setChecked(True)

    def getSpins(self):
        return (self.ui.preSetSpin, self.ui.holdingSpin)

    def setMeta(self, key, **kwargs):
        ## key is 'x' (time), 'y' (amp), or 'xy' (sum)
        self.ui.waveGeneratorWidget.setMeta(key, **kwargs)

    def setUnits(self, units, **kwargs):
        DaqChannelGui.setUnits(self, units)
        self.ui.waveGeneratorWidget.setMeta('y', units=units, siPrefix=True, **kwargs)

    def quit(self):
        DaqChannelGui.quit(self)

        try:
            self.daqUI.sigChanged.disconnect(self.daqChanged)
        except TypeError:
            pass
        self.ui.waveGeneratorWidget.sigDataChanged.disconnect(self.updateWaves)
        self.ui.waveGeneratorWidget.sigFunctionChanged.disconnect(self.waveFunctionChanged)
        self.ui.waveGeneratorWidget.sigParametersChanged.disconnect(self.sequenceChanged)
        self.ui.holdingCheck.stateChanged.disconnect(self.holdingCheckChanged)
        self.ui.holdingSpin.valueChanged.disconnect(self.holdingSpinChanged)
        self.dev.sigHoldingChanged.disconnect(self.updateHolding)

    def functionCheckToggled(self, checked):
        if checked:
            self.ui.waveGeneratorWidget.setEnabled(True)
        else:
            self.ui.waveGeneratorWidget.setEnabled(False)
        self.updateWaves()

    def daqChanged(self, state):
        self.rate = state['rate']
        self.numPts = state['numPts']
        self.timeVals = numpy.linspace(0, float(self.numPts) / self.rate, self.numPts)
        self.updateWaves()

    def listSequence(self):
        return self.ui.waveGeneratorWidget.listSequences()

    def sequenceChanged(self):
        self.sigSequenceChanged.emit(self.dev.name())

    def generateTask(self, params=None):
        if params is None:
            params = {}
        prot = {}
        state = self.stateGroup.state()
        if state['preSetCheck']:
            prot['preset'] = state['preSetSpin']
        if state['holdingCheck']:
            prot['holding'] = state['holdingSpin']
        if state['functionCheck']:
            prot['command'] = self.getSingleWave(params)

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
        ## display sequence waves
        params = {k: list(range(len(ps[k]))) for k in ps}
        waves = []
        runSequence(lambda p: waves.append(self.getSingleWave(p)), params,
                    list(params.keys()))  ## appends waveforms for the entire parameter space to waves

        autoRange = self.plot.getViewBox().autoRangeEnabled()
        self.plot.enableAutoRange(x=False, y=False)
        try:
            for w in waves:
                if w is not None:
                    # self.ui.functionCheck.setChecked(True)
                    self.plotCurve(w, color=Qt.QColor(100, 100, 100))

            ## display single-mode wave in red
            single = self.getSingleWave()
            if single is not None:
                # self.ui.functionCheck.setChecked(True)
                self.plotCurve(single, color=Qt.QColor(200, 100, 100))
        finally:
            self.plot.enableAutoRange(x=autoRange[0], y=autoRange[1])

        self.sigDataChanged.emit(self)

    def taskStarted(self, params):
        ## Draw green trace for current command waveform
        if not self.stateGroup.state()['displayCheck']:
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

    def updateHolding(self):
        hv = self.getHoldingValue()
        if hv is not None:
            if not self.ui.holdingCheck.isChecked():
                self.ui.holdingSpin.setValue(hv)
            self.ui.waveGeneratorWidget.setOffset(hv)

    def getHoldingValue(self):
        """Return the value for this channel that will be used when the task is run
        (by default, this is just the current holding value)"""
        if self.ui.holdingCheck.isChecked():
            return self.ui.holdingSpin.value()
        else:
            return self.taskGui().getChanHolding(self.name)

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
    def __init__(self, parent, name, chanType, units, dev, taskRunner, daqName):
        DaqChannelGui.__init__(self, parent, name, chanType, units, dev, taskRunner, daqName)
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
        return {'record': state['recordCheck'], 'recordInit': state['recordInitCheck']}

    def handleResult(self, result, params):
        if self.stateGroup.state()['displayCheck']:
            if self.clearBeforeNextPlot:
                self.clearPlots()
                self.clearBeforeNextPlot = False

            plot = self.plot.plot(
                y=result.view(numpy.ndarray),
                x=result.xvals('Time'),
                pen=mkPen(200, 200, 200),
                params=params)
