# -*- coding: utf-8 -*-
from __future__ import print_function

import weakref

from acq4.devices.DAQGeneric.DaqChannelGui import DaqMultiChannelTaskGuis
from acq4.devices.Device import TaskGui
from acq4.util import Qt
from pyqtgraph import WidgetGroup


class DAQGenericTaskGui(TaskGui):
    def __init__(self, dev, task, ownUi=True):
        TaskGui.__init__(self, dev, task)
        self.plots = weakref.WeakValueDictionary()
        self.channels = {}
        self.task_gui_generator = DaqMultiChannelTaskGuis(dev, task, ownUi)
        if ownUi:
            self.layout = Qt.QGridLayout()
            self.setLayout(self.layout)
            self.layout.addWidget(self.task_gui_generator.asAWidget())

        else:
            self.stateGroup = None

    def createChannelWidget(self, ch, daqName=None):
        return self.task_gui_generator.createChannelWidget(...)
