# -*- coding: utf-8 -*-
from lib.devices.Device import *
from metaarray import MetaArray, axis
from Mutex import Mutex
import numpy as np
from protoGUI import *
from debug import *
from pyqtgraph import siFormat
import DeviceTemplate


class DataMapping:
    """Class that maps values between the voltages on a DAQ channel and the physically measured units.
    By default, this class applies a simple linear scale and offset for analog channels. Digital channels
    may optionally be inverted.
        Vout = Value * scale - offset
        Value = (Vin + offset) * scale
    This class may be subclassed to allow any arbitrary mapping (eg, calibration curves, etc.)
    """
    def __init__(self, device, chans=None):
        """When mapping initializes, it immediately grabs the scale and offset for each channel
        specified in chans (or all channels if None). This means that the mapping is only valid
        as long as these values have not changed."""
        self.device = device
        self.scale = {}
        self.offset = {}
        if chans is None:
            chans = device.listChannels()
        if type(chans) in [str, unicode]:
            chans = [chans]
        for ch in chans:
            self.scale[ch] = device.getChanScale(ch)
            self.offset[ch] = device.getChanOffset(ch)
            
    def mapToDaq(self, chan, data):
        scale = self.scale[chan]
        offset = self.offset[chan]
        return (data*scale) - offset
        
    def mapFromDaq(self, chan, data):
        scale = self.scale[chan]
        offset = self.offset[chan]
        return (data + offset) * scale
            

class ChannelHandle(object):
    def __init__(self, dev, channel):
        self.dev = dev
        self.channel = channel
        

class DAQGeneric(Device):
    """
    Config format:
    
        ChannelName1:
            device: 'DaqDeviceName'
            channel: '/Dev1/ao0'
            type: 'ao'
            units: 'A'
            scale: 200 * mV / nA
        ChannelName2:
            device: 'DaqDeviceName'
            channel: '/Dev1/ai3'
            type: 'ai'
            mode: 'nrse'
            units: 'A'
            scale: 200 * nA / mV
        ChannelName3:
            device: 'DaqDeviceName'
            channel: '/Dev1/line7'
            type: 'di'
            invert: True
        
    """
    sigHoldingChanged = QtCore.Signal(object, object)
    
    def __init__(self, dm, config, name):
        Device.__init__(self, dm, config, name)
        self._DGLock = Mutex(QtCore.QMutex.Recursive)  ## protects access to _DGHolding, _DGConfig
        ## Do some sanity checks here on the configuration
        self._DGConfig = config
        self._DGHolding = {}
        for ch in config:
            if config[ch]['type'][0] != 'a' and ('scale' in config[ch] or 'offset' in config[ch]):
                raise Exception("Scale/offset only allowed for analog channels. (%s.%s)" % (name, ch))
                
            if 'scale' not in config[ch]:
                config[ch]['scale'] = 1  ## must be int to prevent accidental type conversion on digital data
            if 'offset' not in config[ch]:
                config[ch]['offset'] = 0
            if config[ch].get('invert', False):
                if config[ch]['type'][0] != 'd':
                    raise Exception("Inversion only allowed for digital channels. (%s.%s)" % (name, ch))
                config[ch]['scale'] = -1
                config[ch]['offset'] = -1
                
            #print "chan %s scale %f" % (ch, config[ch]['scale'])
            if 'holding' not in config[ch]:
                config[ch]['holding'] = 0.0
                
            ## It is possible to create virtual channels with no real hardware connection
            if 'device' not in config[ch]:
                #print "Assuming channel %s is virtual:" % ch, config[ch]
                config[ch]['virtual'] = True
                
            ## set holding value for all output channels now
            if config[ch]['type'][1] == 'o':
                self.setChanHolding(ch, config[ch]['holding'])
            #self._DGHolding[ch] = config[ch]['holding']
            
        dm.declareInterface(name, ['daqChannelGroup'], self)
        for ch in config:
            dm.declareInterface(name+"."+ch, ['daqChannel'], ChannelHandle(self, ch))
                            
                            
        
    def mapToDAQ(self, channel, data):
        mapping = self.getMapping(chans=[channel])
        return mapping.mapToDaq(channel, data)
    
    def mapFromDAQ(self, channel, data):
        mapping = self.getMapping(chans=[channel])
        return mapping.mapFromDaq(channel, data)
    
    def getMapping(self, chans=None):
        return DataMapping(self, chans)
            
    def createTask(self, cmd):
        return DAQGenericTask(self, cmd)
    
    def getConfigParam(self, param):
        return self._DGConfig.get(param, None)
    
        
    def setChanHolding(self, channel, level=None, block=True, mapping=None):
        """Define and set the holding values for this channel
        If *block* is True, then return only after the value has been set on the DAQ.
        If *block* is False, then simply schedule the change to take place when the DAQ is available.
        *mapping* is a DataMapping object which tells the device how to translate *level* into
            a voltage on the physical DAQ channel. If *mapping* is None, then it will use self.getMapping(*channel*)
            to determine the correct mapping.
        """
        with self._DGLock:
            #print "set holding", channel, level
            ### Set correct holding level here...
            if level is None:
                level = self._DGHolding[channel]
                if level is None:
                    raise Exception("No remembered holding level for channel %s" % channel)
            else:
                self._DGHolding[channel] = level
                
            if mapping is None:
                mapping = self.getMapping(channel)
            val = mapping.mapToDaq(channel, self._DGHolding[channel])
            #print "Set holding for channel %s: %f => %f" % (channel, self._DGHolding[channel], val)
            
            isVirtual = self._DGConfig[channel].get('virtual', False)
            if not isVirtual:
                daq = self._DGConfig[channel]['device']
                chan = self._DGConfig[channel]['channel']
                daqDev = self.dm.getDevice(daq)
            
        ## release DGLock before setChannelValue
        if not isVirtual:
            if block:
                daqDev.setChannelValue(chan, val, block=True)
            else:
                daqDev.setChannelValue(chan, val, block=False, delaySetIfBusy=True)  ## Note: If a protocol is running, this will not be set until it completes.
        self.sigHoldingChanged.emit(channel, val)
        
    def getChanHolding(self, chan):
        with self._DGLock:
            return self._DGHolding[chan]
        
    def getChannelValue(self, channel, block=True, raw=False):
        with self._DGLock:
            daq = self._DGConfig[channel]['device']
            chan = self._DGConfig[channel]['channel']
            mode = self._DGConfig[channel].get('mode', None)
            
        ## release _DGLock before getChannelValue
        daqDev = self.dm.getDevice(daq)
        val = daqDev.getChannelValue(chan, mode=mode, block=block)
        if not raw:
            return self.mapFromDAQ(channel, val)
        else:
            return val

    def reconfigureChannel(self, chan, config):
        """Allows reconfiguration of channel properties (including the actual DAQ channel name)"""
        with self._DGLock:
            self._DGConfig[chan].update(config)
        
    def deviceInterface(self, win):
        """Return a widget with a UI to put in the device rack"""
        return DAQDevGui(self)
        
    def protocolInterface(self, prot):
        """Return a widget with a UI to put in the protocol rack"""
        return DAQGenericProtoGui(self, prot)

    def getDAQName(self, channel):
        #return self._DGConfig[channel]['channel'][0]
        with self._DGLock:
            return self._DGConfig[channel]['device']

    def quit(self):
        pass

    def setChanScale(self, ch, scale, update=True, block=True):
        with self._DGLock:
            self._DGConfig[ch]['scale'] = scale
        if update and self.isOutput(ch): ## only set Holding for output channels
            self.setChanHolding(ch, block=block)
            
    def setChanOffset(self, ch, offset, update=True, block=True):
        with self._DGLock:
            self._DGConfig[ch]['offset'] = offset
        if update and self.isOutput(ch): ## only set Holding for output channels
            self.setChanHolding(ch, block=block)
            
    def getChanScale(self, chan):
        with self._DGLock:
            ## Scale defaults to 1.0
            ## - can be overridden in configuration
            return self._DGConfig[chan].get('scale', 1.0)

    def getChanOffset(self, chan):
        with self._DGLock:
            ## Offset defaults to 0.0
            ## - can be overridden in configuration
            return self._DGConfig[chan].get('offset', 0.0)

    def getChanUnits(self, ch):
        with self._DGLock:
            if 'units' in self._DGConfig[ch]:
                return self._DGConfig[ch]['units']
            else:
                return None

    def isOutput(self, chan):
        with self._DGLock:
            return self._DGConfig[chan]['type'][1] == 'o'

    def listChannels(self):
        with self._DGLock:
            return dict([(ch, self._DGConfig[ch].copy()) for ch in self._DGConfig])
            
            

class DAQGenericTask(DeviceTask):
    def __init__(self, dev, cmd):
        DeviceTask.__init__(self, dev, cmd)
        self.daqTasks = {}
        self.initialState = {}
        self._DAQCmd = cmd
        ## Stores the list of channels that will generate or acquire buffered samples
        self.bufferedChannels = []
        
    def getConfigOrder(self):
        """return lists of devices that should be configured (before, after) this device"""
        daqs = set([self.dev.getDAQName(ch) for ch in self._DAQCmd])
        return ([], list(daqs))  ## this device should be configured before its DAQs
        
    def configure(self, tasks, startOrder):
        ## Record initial state or set initial value
        ## NOTE:
        ## Subclasses should call this function only _after_ making any changes that will affect the mapping between
        ## physical values and channel voltages.
        
        
        prof = Profiler('DAQGenericTask.configure', disabled=True)
        #self.daqTasks = {}
        self.mapping = self.dev.getMapping(chans=self._DAQCmd.keys())  ## remember the mapping so we can properly translate data after it has been returned
        
        
        self.initialState = {}
        self.holdingVals = {}
        for ch in self._DAQCmd:
            #dev = self.dev.dm.getDevice(self.dev._DGConfig[ch]['channel'][0])
            dev = self.dev.dm.getDevice(self.dev.getDAQName(ch))
            prof.mark(ch+' get dev')
            if 'preset' in self._DAQCmd[ch]:
                with self.dev._DGLock:
                    daqChan = self.dev._DGConfig[ch]['channel']
                #dev.setChannelValue(self.dev._DGConfig[ch]['channel'][1], self._DAQCmd[ch]['preset'])
                preVal = self.mapping.mapToDaq(ch, self._DAQCmd[ch]['preset'])
                dev.setChannelValue(daqChan, preVal)
                prof.mark(ch+' preset')
            elif 'holding' in self._DAQCmd[ch]:
                self.dev.setChanHolding(ch, self._DAQCmd[ch]['holding'])
                prof.mark(ch+' set holding')
            if 'recordInit' in self._DAQCmd[ch] and self._DAQCmd[ch]['recordInit']:
                self.initialState[ch] = self.dev.getChannelValue(ch)
                prof.mark(ch+' record init')
        for ch in self.dev._DGConfig:
            ## record current holding value for all output channels (even those that were not buffered for this task)
            with self.dev._DGLock:
                chanType = self.dev._DGConfig[ch]['type']
            if chanType in ['ao', 'do']:
                self.holdingVals[ch] = self.dev.getChanHolding(ch)
                prof.mark(ch+' record holding')
        prof.finish()
                
    def createChannels(self, daqTask):
        self.daqTasks = {}
        #print "createChannels"
            
        ## Is this the correct DAQ device for any of my channels?
        ## create needed channels + info
        ## write waveform to command channel if needed
            
        chans = self.dev.listChannels()
        for ch in chans:
            #print "  creating channel %s.." % ch
            if ch not in self._DAQCmd:
                #print "    ignoring channel", ch, "not in command"
                continue
            chConf = chans[ch]
            if chConf['device'] != daqTask.devName():
                #print "    ignoring channel", ch, "wrong device"
                continue
            
            ## Input channels are only used if the command has record: True
            if chConf['type'] in ['ai', 'di']:
                #if ('record' not in self._DAQCmd[ch]) or (not self._DAQCmd[ch]['record']):
                if not self._DAQCmd[ch].get('record', False):
                    #print "    ignoring channel", ch, "recording disabled"
                    continue
                
            ## Output channels are only added if they have a command waveform specified
            elif chConf['type'] in ['ao', 'do']:
                if 'command' not in self._DAQCmd[ch]:
                    #print "    ignoring channel", ch, "no command"
                    continue
            
            self.bufferedChannels.append(ch)
            #_DAQCmd[ch]['task'] = daqTask  ## ALSO DON't FORGET TO DELETE IT, ASS.
            if chConf['type'] in ['ao', 'do']:
                #scale = self.getChanScale(ch)
                cmdData = self._DAQCmd[ch]['command']
                if cmdData is None:
                    #print "No command for channel %s, skipping." % ch
                    continue
                #cmdData = cmdData * scale
                    
                ## apply scale, offset or inversion for output lines
                cmdData = self.mapping.mapToDaq(ch, cmdData)
                #print "channel", chConf['channel'][1], cmdData
                
                if chConf['type'] == 'do':
                    cmdData = cmdData.astype(np.uint32)
                    cmdData[cmdData<=0] = 0
                    cmdData[cmdData>0] = 0xFFFFFFFF
                
                #print "channel", self._DAQCmd[ch]
                #print "LOW LEVEL:", self._DAQCmd[ch].get('lowLevelConf', {})
                daqTask.addChannel(chConf['channel'], chConf['type'], **self._DAQCmd[ch].get('lowLevelConf', {}))
                self.daqTasks[ch] = daqTask  ## remember task so we can stop it later on
                daqTask.setWaveform(chConf['channel'], cmdData)
                #print "DO task %s has type" % ch, cmdData.dtype
            elif chConf['type'] == 'ai':
                mode = chConf.get('mode', None)
                #if len(chConf['channel']) > 2:
                    #mode = chConf['channel'][2]
                #print "Adding channel %s to DAQ task" % chConf['channel'][1]
                daqTask.addChannel(chConf['channel'], chConf['type'], mode=mode, **self._DAQCmd[ch].get('lowLevelConf', {}))
                self.daqTasks[ch] = daqTask  ## remember task so we can stop it later on
            elif chConf['type'] == 'di':
                daqTask.addChannel(chConf['channel'], chConf['type'], **self._DAQCmd[ch].get('lowLevelConf', {}))
                self.daqTasks[ch] = daqTask  ## remember task so we can stop it later on
                
        
        
    def getChanUnits(self, chan):
        if 'units' in self._DAQCmd[chan]:
            return self._DAQCmd[chan]['units']
        else:
            return self.dev.getChanUnits(chan)
    
    def start(self):
        ## possibly nothing required here, DAQ will start recording without our help.
        pass
        
    def isDone(self):
        ## DAQ task handles this for us.
        return True
        
    def stop(self, abort=False):
        #with self.dev._DGLock:  ##not necessary
        ## Stop DAQ tasks before setting holding level.
        #print "STOP"
        for ch in self.daqTasks:
            #print "Stop task", ch
            try:
                self.daqTasks[ch].stop(abort=abort)
            except:
                printExc("Error while stopping DAQ task:")
        for ch in self._DAQCmd:
            if 'holding' in self._DAQCmd[ch]:
                self.dev.setChanHolding(ch, self._DAQCmd[ch]['holding'])
            elif self.dev.isOutput(ch):  ## return all output channels to holding value
                self.dev.setChanHolding(ch)
        
    def getResult(self):
        ## Access data recorded from DAQ task
        ## create MetaArray and fill with MC state info
        #self.state['startTime'] = self.daqTasks[self.daqTasks.keys()[0]].getStartTime()
        
        ## Collect data and info for each channel in the command
        #prof = Profiler("  DAQGeneric.getResult")
        result = {}
        #print "buffered channels:", self.bufferedChannels
        for ch in self.bufferedChannels:
            #result[ch] = _DAQCmd[ch]['task'].getData(self.dev.config[ch]['channel'][1])
            result[ch] = self.daqTasks[ch].getData(self.dev._DGConfig[ch]['channel'])
            #prof.mark("get data for channel "+str(ch))
            #print "get data", ch, self.getChanScale(ch), result[ch]['data'].max()
            #scale = self.getChanScale(ch)
            #result[ch]['data'] = result[ch]['data'] / scale
            result[ch]['data'] = self.mapping.mapFromDaq(ch, result[ch]['data']) ## scale/offset/invert
            result[ch]['units'] = self.getChanUnits(ch)
            #print "channel", ch, "returned:\n  ", result[ch]
            #prof.mark("scale data for channel "+str(ch))
            #del _DAQCmd[ch]['task']
        #print "RESULT:", result    
        ## Todo: Add meta-info about channels that were used but unbuffered
        
        
        if len(result) > 0:
            meta = result[result.keys()[0]]['info']
            #print meta
            rate = meta['rate']
            nPts = meta['numPts']
            ## Create an array of time values
            timeVals = np.linspace(0, float(nPts-1) / float(rate), nPts)
            
            ## Concatenate all channels together into a single array, generate MetaArray info
            chanList = [np.atleast_2d(result[x]['data']) for x in result]
            cols = [(x, result[x]['units']) for x in result]
            # print cols
            try:
                arr = np.concatenate(chanList)
            except:
                print chanList
                print [a.shape for a in chanList]
                raise
            
            daqState = {}
            for ch in self.dev._DGConfig:
                if ch in result:
                    daqState[ch] = result[ch]['info']
                else:
                    daqState[ch] = {}
                
                ## record current holding value for all output channels (even those that were not buffered for this task)    
                if self.dev._DGConfig[ch]['type'] in ['ao', 'do']:
                    
                    daqState[ch]['holding'] = self.holdingVals[ch]
            
            info = [axis(name='Channel', cols=cols), axis(name='Time', units='s', values=timeVals)] + [{'DAQ': daqState}]
            
            
            protInfo = self._DAQCmd.copy()  ## copy everything but the command arrays 
            for ch in protInfo:
                if 'command' in protInfo[ch]:
                    del protInfo[ch]['command']
            info[-1]['Protocol'] = protInfo
                
            marr = MetaArray(arr, info=info)
            #print marr
            #prof.mark("post-process data")
            return marr
            
        else:
            return None
            
    def storeResult(self, dirHandle):
        DeviceTask.storeResult(self, dirHandle)
        for ch in self._DAQCmd:
            if self._DAQCmd[ch].get('recordInit', False):
            #if 'recordInit' in self._DAQCmd[ch] and self._DAQCmd[ch]['recordInit']:
                dirHandle.setInfo({(self.dev.name(), ch): self.initialState[ch]})
           
                
class DAQDevGui(QtGui.QWidget):
    def __init__(self, dev):
        self.dev = dev
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        chans = self.dev.listChannels()
        self.widgets = {}
        #self.uis = {}
        self.defaults = {}
        row = 0
        for ch in chans:
            wid = QtGui.QWidget()
            ui = DeviceTemplate.Ui_Form()
            ui.setupUi(wid)
            self.layout.addWidget(wid)
            ui.analogCtrls = [ui.scaleDefaultBtn, ui.scaleSpin, ui.offsetDefaultBtn, ui.offsetSpin, ui.scaleLabel, ui.offsetLabel]
            #ui.channel = ch
            for s in dir(ui):
                i = getattr(ui, s)
                if isinstance(i, QtGui.QWidget):
                    i.channel = ch
                
            self.widgets[ch] = ui
            ui.nameLabel.setText(str(ch))
            ui.channelCombo.addItem("%s (%s)" % (ch, chans[ch]['channel']))
            
            holding = chans[ch].get('holding', 0)
            
            
            
            if chans[ch]['type'] in ['ao', 'ai']:
                ui.inputRadio.setEnabled(False)
                ui.outputRadio.setEnabled(False)
                ui.invertCheck.hide()
                scale = chans[ch].get('scale', 1)
                units = chans[ch].get('units', 'V')
                offset = chans[ch].get('offset', 0)
                ui.offsetSpin.setOpts(suffix = 'V', siPrefix=True, dec=True, step=1.0, minStep=1e-4)
                ui.offsetSpin.setValue(offset)
                ui.offsetSpin.sigValueChanged.connect(self.offsetSpinChanged)
                ui.offsetDefaultBtn.setText("Default (%s)" % siFormat(offset, suffix='V'))
                ui.offsetDefaultBtn.clicked.connect(self.offsetDefaultBtnClicked)
                if chans[ch]['type'] == 'ao':
                    ui.outputRadio.setChecked(True)
                    ui.scaleDefaultBtn.setText("Default (%s)" % siFormat(scale, suffix='V/'+units))
                    ui.scaleSpin.setOpts(suffix= 'V/'+units, siPrefix=True, dec=True, step=1.0, minStep=1e-9)
                    ui.holdingSpin.setOpts(suffix=units, siPrefix=True, step=0.01)
                    ui.holdingSpin.setValue(holding)
                    ui.holdingSpin.sigValueChanged.connect(self.holdingSpinChanged)
                elif chans[ch]['type'] == 'ai':
                    ui.inputRadio.setChecked(True)
                    ui.holdingLabel.hide()
                    ui.holdingSpin.hide()
                    ui.scaleDefaultBtn.setText("Default (%s)" % siFormat(scale, suffix=units+'/V'))
                    #ui.scaleDefaultBtn.clicked.connect(self.scaleDefaultBtnClicked)
                    ui.scaleSpin.setOpts(suffix= units+'/V', siPrefix=True, dec=True)
                ui.scaleSpin.setValue(scale) 
                ui.scaleDefaultBtn.clicked.connect(self.scaleDefaultBtnClicked)
                ui.scaleSpin.sigValueChanged.connect(self.scaleSpinChanged)
                self.defaults[ch] = {
                    'scale': scale,
                    'offset': offset}
            elif chans[ch]['type'] in ['do', 'di']:
                for item in ui.analogCtrls:
                    item.hide()
                if chans[ch].get('invert', False):
                    ui.invertCheck.setChecked(True)
                if chans[ch]['type'] == 'do':
                    ui.outputRadio.setChecked(True)
                    ui.holdingSpin.setOpts(bounds=[0,1], step=1)
                    ui.holdingSpin.setValue(holding)
                    ui.holdingSpin.sigValueChanged.connect(self.holdingSpinChanged)
                elif chans[ch]['type'] == 'di':
                    ui.inputRadio.setChecked(True)
                    ui.holdingLabel.hide()
                    ui.holdingSpin.hide()
                ui.invertCheck.toggled.connect(self.invertToggled)
        #QtCore.QObject.connect(self.dev, QtCore.SIGNAL('holdingChanged'), self.holdingChanged)
        self.dev.sigHoldingChanged.connect(self.holdingChanged)
    
    def holdingChanged(self, ch, val):
        self.widgets[ch].holdingSpin.blockSignals(True)
        self.widgets[ch].holdingSpin.setValue(val)
        self.widgets[ch].holdingSpin.blockSignals(False)
        
    def holdingSpinChanged(self, spin):
        ch = spin.channel
        self.dev.setChanHolding(ch, spin.value(), block=False)
        
    def scaleSpinChanged(self, spin):
        ch = spin.channel
        self.dev.setChanScale(ch, spin.value(), block=False)
    
    def offsetSpinChanged(self, spin):
        ch = spin.channel
        self.dev.setChanOffset(ch, spin.value(), block=False)
        
    def offsetDefaultBtnClicked(self):
        ch = self.sender().channel
        self.widgets[ch].offsetSpin.setValue(self.defaults[ch]['offset'])
        
    def scaleDefaultBtnClicked(self):
        ch = self.sender().channel
        self.widgets[ch].scaleSpin.setValue(self.defaults[ch]['scale'])

    def invertToggled(self, b):
        ch = self.sender().channel
        if b:
            self.dev.setChanScale(ch, -1, update=False)
            self.dev.setChanOffset(ch, 1)
        else:
            self.dev.setChanScale(ch, 1, update=False)
            self.dev.setChanOffset(ch, 0)


