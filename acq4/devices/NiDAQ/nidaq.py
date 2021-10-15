# -*- coding: utf-8 -*-
from __future__ import print_function

import numpy

import acq4.util.Mutex as Mutex
from acq4.devices.BaseDAQ import BaseDAQ
from acq4.devices.Device import Device, DeviceTask
from acq4.devices.NiDAQ.taskGUI import NiDAQTask
from acq4.util.debug import printExc


class NiDAQ(BaseDAQ):
    """
    Config options:
        defaultAIMode: 'mode'  # mode to use for ai channels by default ('rse', 'nrse', or 'diff')
        defaultAIRange: [-10, 10]  # default voltage range to use for AI ports
        defaultAORange: [-10, 10]  # default voltage range to use for AO ports
    """
    def __init__(self, dm, config, name):
        Device.__init__(self, dm, config, name)
        self.config = config
        self._defaultAIRange = config.get('defaultAIRange', [-10, 10])
        self._defaultAORange = config.get('defaultAORange', [-10, 10])

        ## make local copy of device handle
        if config is not None and config.get('mock', False):
            from acq4.drivers.nidaq.mock import NIDAQ
            self.n = NIDAQ
        else:
            from acq4.drivers.nidaq.nidaq import NIDAQ
            self.n = NIDAQ
        print("Created NiDAQ handle, devices are %s" % repr(self.n.listDevices()))
        self.delayedSet = Mutex.threadsafe({})
    
    def createTask(self, cmd, parentTask):
        return Task(self, cmd, parentTask)
        
    def setChannelValue(self, chan, value, block=False, delaySetIfBusy=False, ignoreLock=False):
        """Set a channel on this DAQ. 
        Arguments:
            block: bool. If True, wait until the device is available. 
                   If False, return immediately if the device is not available.
            delaySetIfBusy: If True and the hardware is currently reserved, then
                            schedule the set to occur immediately when the hardware becomes available again.
            ignoreLock: attempt to set the channel value even if the device is reserved.
        Returns True if the channel was set, False otherwise.
        """
        #print "Setting channel %s to %f" % (chan, value)
        if ignoreLock:
            res = True
        else:
            res = self.reserve(block=block)
            
        if not block and not res:
            if delaySetIfBusy:
                #print "  busy, schedule for later."
                self.delayedSet[chan] = value
            return False
        
        try:
            if 'ao' in chan:
                self.n.writeAnalogSample(chan, value, vRange=self._defaultAORange)
            else:
                if value is True or value == 1:
                    value = 0xFFFFFFFF
                else:
                    value = 0
                self.n.writeDigitalSample(chan, value)
        except:
            printExc("Error while setting channel %s to %s:" % (chan, str(value)))
            raise
        finally:
            if not ignoreLock:
                self.release()
        return True

    def release(self):
        ## take care of any channel-value-set requests that arrived while the device was locked
        try:
            self.delayedSet.lock()
            for chan, val in self.delayedSet.items():
                #print "Set delayed:", chan, val
                try:
                    self.setChannelValue(chan, val, ignoreLock=True)
                except Exception:
                    printExc("Error resetting channel value:")
            self.delayedSet.clear()
        finally:
            self.delayedSet.unlock()
        return Device.release(self)

    def getChannelValue(self, chan, mode=None, block=True):
        if mode is None:
            mode = self.config.get('defaultAIMode', None)
        
        res = self.reserve(block=block)
        if not res:  ## False means non-blocking lock attempt failed.
            return False
        #print "Setting channel %s to %f" % (chan, value)
        try:
            if 'ai' in chan:
                val = self.n.readAnalogSample(chan, mode=mode, vRange=self._defaultAIRange)
            else:
                val = self.n.readDigitalSample(chan)
                if val <= 0:
                    val = 0
                else:
                    val = 1
        except:
            printExc("Error while getting channel value %s:" % str(chan))
            raise
        finally:
            self.release()
        return val
        
    def taskInterface(self, taskRunner):
        return NiDAQTask(self, taskRunner)
        
    #def listTriggerPorts(self):
        #p = self.n.listDILines()
        #return [x for x in p if 'PFI' in x]


class Task(DeviceTask):
    def __init__(self, dev, cmd, parentTask):
        DeviceTask.__init__(self, dev, cmd, parentTask)
        self.cmd = cmd
        
        ## get DAQ device
        #daq = self.devm.getDevice(...)
        
        
        ## Create supertask from nidaq driver
        self.st = self.dev.n.createSuperTask()

    def getChanSampleRate(self, ch):
        """Return the sample rate that will be used for ch"""
        
        return self.cmd['rate']  ## currently, all channels use the same rate

    def configure(self):
        #print "daq configure", tasks
        #defaultAIMode = self.dev.config.get('defaultAIMode', None)
        
        ## Request to all devices that they create the channels they use on this task
        tasks = self.parentTask().tasks
        for dName in tasks:
            #print "Requesting %s create channels" % dName
            if hasattr(tasks[dName], 'createChannels'):
                tasks[dName].createChannels(self)
        
        ## If no devices requested buffered operations, then do not configure clock.
        ## This might eventually cause some triggering issues..
        if not self.st.hasTasks():
            return
        
        ## Determine the sample clock source, configure tasks
        self.st.configureClocks(rate=self.cmd['rate'], nPts=self.cmd['numPts'])
        
        ## Determine how the task will be triggered
        if 'triggerChan' in self.cmd:
            self.st.setTrigger(self.cmd['triggerChan'])
        elif 'triggerDevice' in self.cmd:
            tDevName = self.cmd['triggerDevice']
            tDev = self.dev.dm.getDevice(tDevName)
            self.st.setTrigger(tDev.getTriggerChannel(self.dev.name()))
        
    def getStartOrder(self):
        before = []
        after = []
        if 'triggerDevice' in self.cmd:
            after.append(self.cmd['triggerDevice'])
        return before, after
        
    def addChannel(self, channel, type, mode=None, **kwargs):
        #print "Adding channel:", args, kwargs
        ## set default channel mode before adding
        if type == 'ai':
            if mode is None:
                mode = self.dev.config.get('defaultAIMode', None)
            if 'vRange' not in kwargs:
                kwargs['vRange'] = self.dev._defaultAIRange
        elif type == 'ao':
            if 'vRange' not in kwargs:
                kwargs['vRange'] = self.dev._defaultAORange

        return self.st.addChannel(channel, type, mode, **kwargs)
        
    def setWaveform(self, *args, **kwargs):
        return self.st.setWaveform(*args, **kwargs)
        
    def start(self):
        if self.st.hasTasks():
            self.st.start()
        
    def isDone(self):
        if self.st.hasTasks():
            return self.st.isDone()
        else:
            return True

    def stop(self, wait=False, abort=False):
        if self.st.hasTasks():
            #print "stopping ST..."
            self.st.stop(wait=wait, abort=abort)
            #print "   ST stopped"
        
    def getResult(self):
        ## Results should be collected by individual devices using getData
        return None
        
    def storeResult(self, dirHandle):
        pass
        
    def getData(self, channel):
        """Return the data collected for a specific channel. Return looks like:
        {
          'data': ndarray,
          'info': {'rate': xx, 'numPts': xx, ...}
        }
        """
        #prof = Profiler("    NiDAQ.getData")
        res = self.st.getResult(channel)
        data = res['data']
        
            
            
        if 'downsample' in self.cmd:
            ds = self.cmd['downsample']
        else:
            ds = 1
            
        if 'filterMethod' in self.cmd:
            method = self.cmd['filterMethod']
            
            fScale = 0.5 * res['info']['rate'] / ds
            
            if method == 'None':
                pass
            #elif method == 'gaussian':
                #width = self.cmd['gaussianWidth']
                
                #data = scipy.ndimage.gaussian_filter(data, width)
                
                #res['info']['filterMethod'] = method
                #res['info']['filterWidth'] = width
            elif method == 'Bessel':
                cutoff = self.cmd['besselCutoff']
                order = self.cmd['besselOrder']
                bidir = self.cmd.get('besselBidirectional', True)
                data = NiDAQ.lowpass(data, filter='bessel', bidir=bidir, cutoff=cutoff, order=order, samplerate=res['info']['rate'])
                
                res['info']['filterMethod'] = method
                res['info']['filterCutoff'] = cutoff
                res['info']['filterOrder'] = order
                res['info']['filterBidirectional'] = bidir
            elif method == 'Butterworth':
                passF = self.cmd['butterworthPassband']
                stopF = self.cmd['butterworthStopband']
                passDB = self.cmd['butterworthPassDB']
                stopDB = self.cmd['butterworthStopDB']
                bidir = self.cmd.get('butterworthBidirectional', True)
                
                data = NiDAQ.lowpass(data, filter='butterworth', bidir=bidir, cutoff=passF, stopCutoff=stopF, gpass=passDB, gstop=stopDB, samplerate=res['info']['rate'])
                
                res['info']['filterMethod'] = method
                res['info']['filterPassband'] = passF
                res['info']['filterStopband'] = stopF
                res['info']['filterPassbandDB'] = passDB
                res['info']['filterStopbandDB'] = stopDB
                res['info']['filterBidirectional'] = bidir
                
            else:
                printExc("Unknown filter method '%s'" % str(method))
                
        
        if ds > 1:
        
            if res['info']['type'] in ['di', 'do']:
                res['data'] = (res['data'] > 0).astype(numpy.byte)
                dsMethod = 'subsample'
                data = data[::ds]
                res['info']['downsampling'] = ds
                res['info']['downsampleMethod'] = 'subsample'
                res['info']['rate'] = res['info']['rate'] / ds
            elif res['info']['type'] in ['ai', 'ao']:
                data = NiDAQ.meanResample(data, ds)
                res['info']['downsampling'] = ds
                res['info']['downsampleMethod'] = 'mean'
                res['info']['rate'] = res['info']['rate'] / ds
            else:
                dsMethod = None

        if 'denoiseMethod' in self.cmd:
            method = self.cmd['denoiseMethod']
            if method == 'None':
                pass
            elif method == 'Pointwise':
                width = self.cmd['denoiseWidth']
                thresh = self.cmd['denoiseThreshold']
                
                res['info']['denoiseMethod'] = method
                res['info']['denoiseWidth'] = width
                res['info']['denoiseThreshold'] = thresh
                data = NiDAQ.denoise(data, width, thresh)
            else:
                printExc("Unknown denoise method '%s'" % str(method))

                
        res['data'] = data
        res['info']['numPts'] = data.shape[0]
                
        return res
        
    def devName(self):
        return self.dev.name()
