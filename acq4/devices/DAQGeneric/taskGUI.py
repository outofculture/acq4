# -*- coding: utf-8 -*-
from __future__ import print_function

import weakref

from acq4.devices.DAQGeneric import DAQGeneric
from acq4.devices.DAQGeneric.DaqChannelGui import DaqMultiChannelTaskGuis
from acq4.devices.Device import TaskGui
from acq4.util import Qt


class DAQGenericTaskGui(TaskGui):
    def __init__(self, dev: DAQGeneric, task, ownUi=True):
        TaskGui.__init__(self, dev, task)
        self.plots = weakref.WeakValueDictionary()
        self.channels = {}
        self.task_gui_generator = DaqMultiChannelTaskGuis(dev, task)
        if ownUi:
            self.layout = Qt.QGridLayout()
            self.setLayout(self.layout)
            self.layout.addWidget(self.task_gui_generator.asAWidget())

        else:
            self.stateGroup = None

    def createChannelWidget(self, ch):
        units = self.dev.getChanUnits(ch)
        chanType = self.dev.getChanType(ch)
        return self.task_gui_generator.createChannelWidget(ch, chanType, units)
