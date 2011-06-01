# -*- coding: utf-8 -*-
from __future__ import with_statement
from PatchTemplate import *
from PyQt4 import QtGui, QtCore
#from PyQt4 import Qwt5 as Qwt
from WidgetGroup import WidgetGroup
from pyqtgraph.PlotWidget import PlotWidget
from metaarray import *
from Mutex import Mutex, MutexLocker
import traceback, sys, time
from numpy import *
import scipy.optimize
from debug import *
from functions import siFormat
from lib.Manager import getManager


class PatchWindow(QtGui.QMainWindow):
    def __init__(self, dm, clampName):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(clampName)
        self.startTime = None
        self.redrawCommand = 1
        
        self.analysisItems = {
            'inputResistance': u'Ω', 
            'accessResistance': u'Ω',
            'capacitance': 'F',
            'restingPotential': 'V', 
            'restingCurrent': 'A', 
            'fitError': ''
        }
        
        self.params = {
            'mode': 'vc',
            'rate': 200000,
            'downsample': 20,
            'cycleTime': .2,
            'recordTime': 0.1,
            'delayTime': 0.03,
            'pulseTime': 0.05,
            'icPulse': -30e-12,
            'vcPulse': -10e-3,
            'icHolding': 0,
            'vcHolding': -50e-3,
            'icHoldingEnabled': False,
            'icPulseEnabled': True,
            'vcHoldingEnabled': False,
            'vcPulseEnabled': True,
            'drawFit': True,
            'average': 1,
        }
        
        
        self.paramLock = Mutex(QtCore.QMutex.Recursive)

        self.manager = dm
        self.clampName = clampName
        self.thread = PatchThread(self)
        self.cw = QtGui.QWidget()
        self.setCentralWidget(self.cw)
        self.ui = Ui_Form()
        self.ui.setupUi(self.cw)

        self.stateFile = os.path.join('modules', self.clampName + '_ui.cfg')
        uiState = getManager().readConfigFile(self.stateFile)
        if 'geometry' in uiState:
            geom = QtCore.QRect(*uiState['geometry'])
            self.setGeometry(geom)
        if 'window' in uiState:
            ws = QtCore.QByteArray.fromPercentEncoding(uiState['window'])
            self.restoreState(ws)


        self.plots = {}
        for k in self.analysisItems:
            p = PlotWidget()
            p.setLabel('left', text=k, units=self.analysisItems[k])
            self.ui.plotLayout.addWidget(p)
            self.plots[k] = p
        #irp = self.plots['inputResistance']
        #irp.setManualYScale()
        #irp.setYLog(True)
        #irp.setYRange(1e6, 1e11)
            
        
        self.ui.icPulseSpin.setOpts(dec=True, step=1, minStep=1e-12, bounds=[None,None], siPrefix=True, suffix='A')
        self.ui.vcPulseSpin.setOpts(dec=True, step=1, minStep=1e-3, bounds=[None,None], siPrefix=True, suffix='V')
        self.ui.icHoldSpin.setOpts(dec=True, step=1, minStep=1e-12, bounds=[None,None], siPrefix=True, suffix='A')
        self.ui.vcHoldSpin.setOpts(dec=True, step=1, minStep=1e-3, bounds=[None,None], siPrefix=True, suffix='V')
        self.ui.cycleTimeSpin.setOpts(dec=True, step=1, minStep=1e-6, bounds=[0,None], siPrefix=True, suffix='s')
        self.ui.pulseTimeSpin.setOpts(dec=True, step=1, minStep=1e-6, bounds=[0,1.], siPrefix=True, suffix='s')
        self.ui.delayTimeSpin.setOpts(dec=True, step=1, minStep=1e-6, bounds=[0,1.], siPrefix=True, suffix='s')
        
        
        self.stateGroup = WidgetGroup([
            (self.ui.icPulseSpin, 'icPulse'),
            (self.ui.vcPulseSpin, 'vcPulse'),
            (self.ui.icHoldSpin, 'icHolding'),
            (self.ui.vcHoldSpin, 'vcHolding'),
            (self.ui.icPulseCheck, 'icPulseEnabled'),
            (self.ui.vcPulseCheck, 'vcPulseEnabled'),
            (self.ui.icHoldCheck, 'icHoldingEnabled'),
            (self.ui.vcHoldCheck, 'vcHoldingEnabled'),
            (self.ui.cycleTimeSpin, 'cycleTime'),
            (self.ui.pulseTimeSpin, 'pulseTime'),
            (self.ui.delayTimeSpin, 'delayTime'),
            (self.ui.drawFitCheck, 'drawFit'),
            (self.ui.averageSpin, 'average'),
        ])
        #self.stateGroup = WidgetGroup([
        #    (self.ui.icPulseSpin, 'icPulse', 1e12),
        #    (self.ui.vcPulseSpin, 'vcPulse', 1e3),
        #    (self.ui.icHoldSpin, 'icHolding', 1e12),
        #    (self.ui.vcHoldSpin, 'vcHolding', 1e3),
        #    (self.ui.icPulseCheck, 'icPulseEnabled'),
        #    (self.ui.vcPulseCheck, 'vcPulseEnabled'),
        #    (self.ui.icHoldCheck, 'icHoldingEnabled'),
        #    (self.ui.vcHoldCheck, 'vcHoldingEnabled'),
        #    (self.ui.cycleTimeSpin, 'cycleTime', 1),
        #    (self.ui.pulseTimeSpin, 'pulseTime', 1e3),
        #    (self.ui.delayTimeSpin, 'delayTime', 1e3),
        #])
        self.stateGroup.setState(self.params)
        
        self.ui.patchPlot.setLabel('left', text='Primary', units='A')
        self.patchCurve = self.ui.patchPlot.plot(pen=QtGui.QPen(QtGui.QColor(200, 200, 200)))
        self.patchFitCurve = self.ui.patchPlot.plot(pen=QtGui.QPen(QtGui.QColor(0, 100, 200)))
        self.ui.commandPlot.setLabel('left', text='Secondary', units='V')
        self.commandCurve = self.ui.commandPlot.plot(pen=QtGui.QPen(QtGui.QColor(200, 200, 200)))
        
        #QtCore.QObject.connect(self.ui.startBtn, QtCore.SIGNAL('clicked()'), self.startClicked)
        self.ui.startBtn.clicked.connect(self.startClicked)
        #QtCore.QObject.connect(self.ui.recordBtn, QtCore.SIGNAL('clicked()'), self.recordClicked)
        self.ui.recordBtn.clicked.connect(self.recordClicked)
        #QtCore.QObject.connect(self.ui.bathModeBtn, QtCore.SIGNAL('clicked()'), self.bathMode)
        self.ui.bathModeBtn.clicked.connect(self.bathMode)
        #QtCore.QObject.connect(self.ui.patchModeBtn, QtCore.SIGNAL('clicked()'), self.patchMode)
        self.ui.patchModeBtn.clicked.connect(self.patchMode)
        #QtCore.QObject.connect(self.ui.cellModeBtn, QtCore.SIGNAL('clicked()'), self.cellMode)
        self.ui.cellModeBtn.clicked.connect(self.cellMode)
        #QtCore.QObject.connect(self.ui.monitorModeBtn, QtCore.SIGNAL('clicked()'), self.monitorMode)
        self.ui.monitorModeBtn.clicked.connect(self.monitorMode)
        #QtCore.QObject.connect(self.ui.resetBtn, QtCore.SIGNAL('clicked()'), self.resetClicked)
        self.ui.resetBtn.clicked.connect(self.resetClicked)
        #QtCore.QObject.connect(self.thread, QtCore.SIGNAL('finished()'), self.threadStopped)
        self.thread.finished.connect(self.threadStopped)
        #QtCore.QObject.connect(self.thread, QtCore.SIGNAL('newFrame'), self.handleNewFrame)
        self.thread.sigNewFrame.connect(self.handleNewFrame)
        #QtCore.QObject.connect(self.ui.icModeRadio, QtCore.SIGNAL('toggled(bool)'), self.updateParams)
        #QtCore.QObject.connect(self.ui.vcModeRadio, QtCore.SIGNAL('toggled(bool)'), self.updateParams)
        self.ui.vcModeRadio.toggled.connect(self.updateParams)
        #QtCore.QObject.connect(self.stateGroup, QtCore.SIGNAL('changed'), self.updateParams)
        self.stateGroup.sigChanged.connect(self.updateParams)
                
        ## Configure analysis plots, curves, and data arrays
        self.analysisCurves = {}
        self.analysisData = {'time': []}
        for n in self.analysisItems:
            w = getattr(self.ui, n+'Check')
            #QtCore.QObject.connect(w, QtCore.SIGNAL('clicked()'), self.showPlots)
            w.clicked.connect(self.showPlots)
            p = self.plots[n]
            #p.setCanvasBackground(QtGui.QColor(0,0,0))
            #p.replot()
            self.analysisCurves[n] = p.plot(pen=QtGui.QPen(QtGui.QColor(200, 200, 200)))
            for suf in ['', 'Std']:
                #self.analysisCurves[n+suf] = p.plot(pen=QtGui.QPen(QtGui.QColor(200, 200, 200)), replot=False)
                #self.analysisCurves[n+suf] = PlotCurve(n+suf)
                #self.analysisCurves[n+suf].setPen(QtGui.QPen(QtGui.QColor(200, 200, 200)))
                #self.analysisCurves[n+suf].attach(p)
                self.analysisData[n+suf] = []
        self.showPlots()
        self.updateParams()
        self.show()
    
    def quit(self):
        #print "Stopping patch thread.."
        geom = self.geometry()
        uiState = {'window': str(self.saveState().toPercentEncoding()), 'geometry': [geom.x(), geom.y(), geom.width(), geom.height()]}
        getManager().writeConfigFile(uiState, self.stateFile)
        
        self.thread.stop(block=True)
        #print "Patch thread exited; module quitting."
        
    def closeEvent(self, ev):
        self.quit()
    
    def bathMode(self):
        self.ui.vcPulseCheck.setChecked(True)
        self.ui.vcHoldCheck.setChecked(False)
        self.ui.vcModeRadio.setChecked(True)
        self.ui.cycleTimeSpin.setValue(0.2)
        self.ui.pulseTimeSpin.setValue(50e-3)
        self.ui.averageSpin.setValue(1)
    
    def patchMode(self):
        self.ui.vcPulseCheck.setChecked(True)
        self.ui.vcHoldCheck.setChecked(True)
        self.ui.vcModeRadio.setChecked(True)
        self.ui.cycleTimeSpin.setValue(0.2)
        self.ui.pulseTimeSpin.setValue(50e-3)
        self.ui.averageSpin.setValue(1)
    
    def cellMode(self):
        self.ui.icPulseCheck.setChecked(True)
        self.ui.icModeRadio.setChecked(True)
        self.ui.cycleTimeSpin.setValue(250e-3)
        self.ui.pulseTimeSpin.setValue(150e-3)
        self.ui.averageSpin.setValue(1)

    def monitorMode(self):
        self.ui.cycleTimeSpin.setValue(20)
        self.ui.averageSpin.setValue(10)
        
    def showPlots(self):
        """Show/hide analysis plot widgets"""
        for n in self.analysisItems:
            w = getattr(self.ui, n+'Check')
            p = self.plots[n]
            if w.isChecked():
                p.show()
            else:
                p.hide()
        self.updateAnalysisPlots()
    
    def updateParams(self, *args):
        with self.paramLock:
            if self.ui.icModeRadio.isChecked():
                mode = 'ic'
            else:
                mode = 'vc'
            self.params['mode'] = mode
            state = self.stateGroup.state()
            for p in self.params:
                if p in state:
                    self.params[p] = state[p]
            self.params['recordTime'] = self.params['delayTime'] *2.0 + self.params['pulseTime']
        self.thread.updateParams()
        self.redrawCommand = 2   ## may need to redraw twice to make sure the update has gone through
        
    def recordClicked(self):
        if self.ui.recordBtn.isChecked():
            data = self.makeAnalysisArray()
            if data.shape[0] == 0:  ## no data yet; don't start the file
                self.storageFile = None
                return
            self.newFile(data)
        else:
            self.storageFile = None
            
    def newFile(self, data):
        sd = self.storageDir()
        self.storageFile = sd.writeFile(data, self.clampName, autoIncrement=True, appendAxis='Time', newFile=True)
        if self.startTime is not None:
            self.storageFile.setInfo({'startTime': self.startTime})
                
    def storageDir(self):
        return self.manager.getCurrentDir().getDir('Patch', create=True)
                
    #def storageFile(self):
        #sd = self.storageDir()
        #return sd.getFile(self.clampName, create=True)
            
        
    def resetClicked(self):
        self.ui.recordBtn.setChecked(False)
        self.recordClicked()
        for n in self.analysisData:
            self.analysisData[n] = []
        self.startTime = None
        
    def handleNewFrame(self, frame):
        prof = Profiler('PatchWindow.handleNewFrame', disabled=True)
        with self.paramLock:
            mode = self.params['mode']
        
        data = frame['data'][self.clampName]
        
        if mode == 'vc':
            self.ui.patchPlot.setLabel('left', units='A')
            #self.ui.commandPlot.setLabel('left', units='V')
            #scale1 = 1e12
            #scale2 = 1e3
        else:
            self.ui.patchPlot.setLabel('left', units='V')
            #self.ui.commandPlot.setLabel('left', units='A')
            #scale1 = 1e3
            #scale2 = 1e12
        prof.mark('1')
            
        self.patchCurve.setData(data.xvals('Time'), data['primary'])
        prof.mark('2')
        if self.redrawCommand > 0:
            self.redrawCommand -= 1
            #print "set command curve"
            self.commandCurve.setData(data.xvals('Time'), data['command'])
            if mode == 'vc':
                self.ui.commandPlot.setLabel('left', units='V')
            else:
                self.ui.commandPlot.setLabel('left', units='A')
        prof.mark('3')
        #self.ui.patchPlot.replot()
        #self.ui.commandPlot.replot()
        if frame['analysis']['fitTrace'] is not None:
            self.patchFitCurve.show()
            self.patchFitCurve.setData(data.xvals('Time'), frame['analysis']['fitTrace'])
        else:
            self.patchFitCurve.hide()
        prof.mark('4')
        
        for k in self.analysisItems:
            if k in frame['analysis']:
                self.analysisData[k].append(frame['analysis'][k])
        prof.mark('5')
                
        for r in ['input', 'access']:
            res = r+'Resistance'
            label = getattr(self.ui, res+'Label')
            resistance = frame['analysis'][res]
            label.setText(siFormat(resistance) + u'Ω')
        prof.mark('6')
        self.ui.restingPotentialLabel.setText(siFormat(frame['analysis']['restingPotential'], error=frame['analysis']['restingPotentialStd'], suffix='V'))
        self.ui.restingCurrentLabel.setText(siFormat(frame['analysis']['restingCurrent'], error=frame['analysis']['restingCurrentStd'], suffix='A'))
        self.ui.capacitanceLabel.setText('%sF' % siFormat(frame['analysis']['capacitance']))
        self.ui.fitErrorLabel.setText('%7.2g' % frame['analysis']['fitError'])
        prof.mark('7')
        
        start = data._info[-1]['DAQ']['command']['startTime']
        if self.startTime is None:
            self.startTime = start
            if self.ui.recordBtn.isChecked() and self.storageFile is not None:
                self.storageFile.setInfo({'startTime': self.startTime})
        self.analysisData['time'].append(start - self.startTime)
        prof.mark('8')
        self.updateAnalysisPlots()
        prof.mark('9')
        
        ## Record to disk if requested.
        if self.ui.recordBtn.isChecked():
            
            arr = self.makeAnalysisArray(lastOnly=True)
            #print "appending array", arr.shape
            if self.storageFile is None:
                self.newFile(arr)
            else:
                arr.write(self.storageFile.name(), appendAxis='Time')
        prof.mark('10')
        prof.finish()
        
    def makeAnalysisArray(self, lastOnly=False):
        ## Determine how much of the data to include in this array
        if lastOnly:
            sl = slice(-1, None)
        else:
            sl = slice(None)
            
        ## Generate the meta-info structure
        info = [
            {'name': 'Time', 'values': self.analysisData['time'][sl], 'units': 's'},
            {'name': 'Value', 'cols': []}
        ]
        for k in self.analysisItems:
            for s in ['', 'Std']:
                if len(self.analysisData[k+s]) < 1:
                    continue
                info[1]['cols'].append({'name': k+s, 'units': self.analysisItems[k]})
                
        ## Create the blank MetaArray
        data = MetaArray(
            (len(info[0]['values']), len(info[1]['cols'])), 
            dtype=float,
            info=info
        )
        
        ## Fill with data
        for k in self.analysisItems:
            for s in ['', 'Std']:
                if len(self.analysisData[k+s]) < 1:
                    continue
                try:
                    data[:, k+s] = self.analysisData[k+s][sl]
                except:
                    print data.shape, data[:, k+s].shape, len(self.analysisData[k+s][sl])
                    raise
                
        return data
            
            
        
    def updateAnalysisPlots(self):
        for n in self.analysisItems:
            p = self.plots[n]
            if p.isVisible():
                self.analysisCurves[n].setData(self.analysisData['time'], self.analysisData[n])
                #if len(self.analysisData[n+'Std']) > 0:
                    #self.analysisCurves[p+'Std'].setData(self.analysisData['time'], self.analysisData[n+'Std'])
                #p.replot()
    
    def startClicked(self):
        if self.ui.startBtn.isChecked():
            if not self.thread.isRunning():
                self.thread.start()
            self.ui.startBtn.setText('Stop')
        else:
            self.ui.startBtn.setEnabled(False)
            self.thread.stop()
            
    def threadStopped(self):
        self.ui.startBtn.setText('Start')
        self.ui.startBtn.setEnabled(True)
        self.ui.startBtn.setChecked(False)
        
        
class PatchThread(QtCore.QThread):
    
    sigNewFrame = QtCore.Signal(object)
    
    def __init__(self, ui):
        self.ui = ui
        self.manager = ui.manager
        self.clampName = ui.clampName
        QtCore.QThread.__init__(self)
        self.lock = Mutex(QtCore.QMutex.Recursive)
        self.stopThread = True
        self.paramsUpdated = True
    
    def updateParams(self):
        with self.lock:
            self.paramsUpdated = True
    
    def run(self):
        """Main loop for patch thread. This is where protocols are executed and data collected."""
        try:
            with MutexLocker(self.lock) as l:
                self.stopThread = False
                clamp = self.manager.getDevice(self.clampName)
                daqName = clamp.listChannels().values()[0]['channel'][0]  ## Just guess the DAQ by checking one of the clamp's channels
                clampName = self.clampName
                self.paramsUpdated = True
                l.unlock()
                
                lastTime = None
                while True:
                    prof = Profiler('PatchThread.run', disabled=True)
                    lastTime = time.clock()
                    
                    updateCommand = False
                    l.relock()
                    if self.paramsUpdated:
                        with self.ui.paramLock:
                            params = self.ui.params.copy()
                            self.paramsUpdated = False
                        updateCommand = True
                    l.unlock()
                    
                    ## Regenerate command signal if parameters have changed
                    numPts = int(float(params['recordTime']) * params['rate'])
                    mode = params['mode']
                    if params[mode+'HoldingEnabled']:
                        holding = params[mode+'Holding']
                    else:
                        holding = 0.
                    if params[mode+'PulseEnabled']:
                        amplitude = params[mode+'Pulse']
                    else:
                        amplitude = 0.
                    cmdData = empty(numPts)
                    cmdData[:] = holding
                    start = int(params['delayTime'] * params['rate'])
                    stop = start + int(params['pulseTime'] * params['rate'])
                    cmdData[start:stop] = holding + amplitude
                    #cmdData[-1] = holding
                    
                    cmd = {
                        'protocol': {'duration': params['recordTime'], 'leadTime': 0.02},
                        daqName: {'rate': params['rate'], 'numPts': numPts, 'downsample': params['downsample']},
                        clampName: {
                            'mode': params['mode'],
                            'command': cmdData,
                            'holding': holding
                        }
                        
                    }
                    prof.mark('build command')
                    
                    ## Create and execute task.
                    ## the try/except block is just to catch errors that come up during multiclamp auto pipette offset procedure.
                    results = []
                    for i in range(params['average']):
                        exc = False
                        count = 0
                        while not exc:
                            count += 1
                            try:
                                ## Create task
                                task = self.manager.createTask(cmd)
                                ## Execute task
                                task.execute()
                                exc = True
                            except:
                                err = sys.exc_info()[1].args
                                #print err
                                if count < 5 and len(err) > 1 and err[1] == 'ExtCmdSensOff':  ## external cmd sensitivity is off, wait to see if it comes back..
                                    time.sleep(1.0)
                                    continue
                                else:
                                    raise
                        #print cmd
                        
                        ## analyze trace 
                        result = task.getResult()
                        #print result
                        results.append(result)
                        
                    prof.mark('execute')
                        
                    ## average together results if we collected more than 1
                    if len(results) == 1:
                        result = results[0]
                        avg = result[clampName]
                    else:
                        avg = concatenate([res[clampName].view(ndarray)[newaxis, ...] for res in results], axis=0).mean(axis=0)
                        avg = MetaArray(avg, info=results[0][clampName].infoCopy())
                        result = results[0]
                        result[clampName] = avg
                    #print result[clampName]['primary'].max(), result[clampName]['primary'].min()
                    
                    #print result[clampName]
                    analysis = self.analyze(avg, params)
                    frame = {'data': result, 'analysis': analysis}
                    prof.mark('analyze')
                    
                    #self.emit(QtCore.SIGNAL('newFrame'), frame)
                    self.sigNewFrame.emit(frame)
                    
                    ## sleep until it is time for the next run
                    c = 0
                    stop = False
                    while True:
                        ## check for stop button every 100ms
                        if c % 10 == 0:
                            l.relock()
                            if self.stopThread:
                                l.unlock()
                                stop = True
                                break
                            l.unlock()
                        now = time.clock()
                        if now >= (lastTime+params['cycleTime']):
                            break
                        
                        time.sleep(10e-3) ## Wake up every 10ms
                        c += 1
                    if stop:
                        break
                    prof.mark('wait')
        except:
            printExc("Error in patch acquisition thread, exiting.")
        #self.emit(QtCore.SIGNAL('threadStopped'))
            
    def analyze(self, data, params):
        #print "\n\nAnalysis parameters:", params
        ## Extract specific time segments
        nudge = 0.1e-3
        base = data['Time': 0.0:(params['delayTime']-nudge)]
        pulse = data['Time': params['delayTime']+nudge:params['delayTime']+params['pulseTime']-nudge]
        pulseEnd = data['Time': params['delayTime']+(params['pulseTime']*2./3.):params['delayTime']+params['pulseTime']-nudge]
        end = data['Time':params['delayTime']+params['pulseTime']+nudge:]
        #print "time ranges:", pulse.xvals('Time').min(),pulse.xvals('Time').max(),end.xvals('Time').min(),end.xvals('Time').max()
        ## Exponential fit
        #  v[0] is offset to start of exp
        #  v[1] is amplitude of exp
        #  v[2] is tau
        def expFn(v, t):
            return (v[0]-v[1]) + v[1] * exp(-t / v[2])
        # predictions
        ar = 10e6
        ir = 200e6
        if params['mode'] == 'vc':
            ari = params['vcPulse'] / ar
            iri = params['vcPulse'] / ir
            pred1 = [ari, ari-iri, 1e-3]
            pred2 = [iri-ari, iri-ari, 1e-3]
        else:
            #clamp = self.manager.getDevice(self.clampName)
            try:
                bridge = data._info[-1]['ClampState']['ClampParams']['BridgeBalResist']
                bridgeOn = data._info[-1]['ClampState']['ClampParams']['BridgeBalEnabled']
                #bridge = float(clamp.getParam('BridgeBalResist'))  ## pull this from the data instead.
                #bridgeOn = clamp.getParam('BridgeBalEnable')
                if not bridgeOn:
                    bridge = 0.0
            except:
                bridge = 0.0
            #print "bridge:", bridge
            arv = params['icPulse'] * ar - bridge
            irv = params['icPulse'] * ir
            pred1 = [arv, -irv, 10e-3]
            pred2 = [irv, irv, 50e-3]
            
        # Fit exponential to pulse and post-pulse traces
        tVals1 = pulse.xvals('Time')-pulse.xvals('Time').min()
        tVals2 = end.xvals('Time')-end.xvals('Time').min()
        
        baseMean = base['primary'].mean()
        fit1 = scipy.optimize.leastsq(
            lambda v, t, y: y - expFn(v, t), pred1, 
            args=(tVals1, pulse['primary'] - baseMean),
            maxfev=200, full_output=1)
        #fit2 = scipy.optimize.leastsq(
            #lambda v, t, y: y - expFn(v, t), pred2, 
            #args=(tVals2, end['primary'] - baseMean),
            #maxfev=200, full_output=1, warning=False)
            
        
        #err = max(abs(fit1[2]['fvec']).sum(), abs(fit2[2]['fvec']).sum())
        err = abs(fit1[2]['fvec']).sum()
        
        
        # Average fit1 with fit2 (needs massaging since fits have different starting points)
        #print fit1
        fit1 = fit1[0]
        #fit2 = fit2[0]
        #fitAvg = [   ## Let's just not do this.
            #0.5 * (fit1[0] - (fit2[0] - (fit1[0] - fit1[1]))),
            #0.5 * (fit1[1] - fit2[1]),
            #0.5 * (fit1[2] + fit2[2])            
        #]
        fitAvg = fit1

        (fitOffset, fitAmp, fitTau) = fit1
        #print fit1
        
        fitTrace = empty(len(data))
        
        ## Handle analysis differently depenting on clamp mode
        if params['mode'] == 'vc':
            #global iBase, iPulse, iPulseEnd
            iBase = base['Channel': 'primary']
            iPulse = pulse['Channel': 'primary'] 
            iPulseEnd = pulseEnd['Channel': 'primary'] 
            vBase = base['Channel': 'command']
            vPulse = pulse['Channel': 'command'] 
            vStep = vPulse.mean() - vBase.mean()
            sign = [-1, 1][vStep > 0]

            iStep = sign * max(1e-15, sign * (iPulseEnd.mean() - iBase.mean()))
            iRes = vStep / iStep
            
            ## From Santos-Sacchi 1993
            pTimes = pulse.xvals('Time')
            iCapEnd = pTimes[-1]
            iCap = iPulse['Time':pTimes[0]:iCapEnd] - iPulseEnd.mean()
            Q = sum(iCap) * (iCapEnd - pTimes[0]) / iCap.shape[0]
            Rin = iRes
            Vc = vStep
            Rs_denom = (Q * Rin + fitTau * Vc)
            if Rs_denom != 0.0:
                Rs = (Rin * fitTau * Vc) / Rs_denom
                Rm = Rin - Rs
                Cm = (Rin**2 * Q) / (Rm**2 * Vc)
            else:
                Rs = 0
                Rm = 0
                Cm = 0
            aRes = Rs
            cap = Cm
            
        if params['mode'] == 'ic':
            iBase = base['Channel': 'command']
            iPulse = pulse['Channel': 'command'] 
            vBase = base['Channel': 'primary']
            vPulse = pulse['Channel': 'primary'] 
            vPulseEnd = pulseEnd['Channel': 'primary'] 
            iStep = iPulse.mean() - iBase.mean()
            
            if iStep >= 0:
                vStep = max(1e-5, -fitAmp)
            else:
                vStep = min(-1e-5, -fitAmp)
            #sign = [-1, 1][iStep >= 0]
            #vStep = sign * max(1e-5, sign * (vPulseEnd.mean() - vBase.mean()))
            #vStep = sign * max(1e-5, sign * fitAmp)
            if iStep == 0:
                iStep = 1e-14
            iRes = (vStep / iStep)
            #print iRes, vStep, iStep, bridge
            #print "current step:", iStep
            #print "bridge:", bridge
            aRes = (fitOffset / iStep) + bridge
            #iRes = (-fitAvg[1] / iStep) + bridge
            cap = fitTau / iRes
            
            
        rmp = vBase.mean()
        rmps = vBase.std()
        rmc = iBase.mean()
        rmcs = iBase.std()
        #print rmp, rmc
        
        ## Compute values for fit trace to be plotted over raw data
        if params['drawFit']:
            fitTrace = MetaArray((data.shape[1],), info=[{'name': 'Time', 'values': data.xvals('Time')}])
            if params['mode'] == 'vc':
                fitTrace[:] = rmc
            else:
                fitTrace[:] = rmp
    #        print i1, i2, len(tVals1), len(tVals2), len(expFn(fit1, tVals2)), len(fitTrace[i2:])
            ## slices from fitTrace must exactly match slices from data at the beginning of the function.
            fitTrace['Time': params['delayTime']+nudge:params['delayTime']+params['pulseTime']-nudge] = expFn(fit1, tVals1)+baseMean
            #fitTrace['Time':params['delayTime']+params['pulseTime']+nudge:] = expFn(fit2, tVals2)+baseMean
        else:
            fitTrace = None
        
        
        
            
        return {
            'inputResistance': iRes, 
            'accessResistance': aRes,
            'capacitance': cap,
            'restingPotential': rmp, 'restingPotentialStd': rmps,
            'restingCurrent': rmc, 'restingCurrentStd': rmcs,
            'fitError': err,
            'fitTrace': fitTrace
        }
            
    def stop(self, block=False):
        with self.lock:
            self.stopThread = True
        if block:
            if not self.wait(10000):
                raise Exception("Timed out while waiting for patch thread exit!")
                
