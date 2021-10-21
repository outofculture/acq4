from acq4.util.DaqChannelGui import DaqMultiChannelTaskGuis
from pyqtgraph.Qt import mkQApp
from acq4.util import Qt
from pyqtgraph.parametertree import ParameterTree, Parameter

app = mkQApp()

win = Qt.QSplitter(Qt.Qt.Horizontal)

param = Parameter.create(name='params', type='group', children=[
    {'name': 'sample rate', 'type': 'int', 'value': 10000},
    {'name': 'num samples', 'type': 'int', 'value': 1000},
    {'name': 'save', 'type': 'action'},
    {'name': 'load', 'type': 'action'},
])

paramTree = ParameterTree()
paramTree.setParameters(param, showTop=False)
win.addWidget(paramTree)

ui_maker = DaqMultiChannelTaskGuis("Monster Palace")
ui_maker.createChannelWidget("rat_out", "ao", "squeaks")
ui_maker.createChannelWidget("rat_in", "ai", "cheeses")
ui_maker.createChannelWidget("robot_out", "do", "beeps")
ui_maker.createChannelWidget("robot_in", "di", "bops")


def updateChannels():
    ui_maker.daqStateChanged({"rate": param['sample rate'], "numPts": param['num samples']})


savedState = None


def save():
    global savedState
    savedState = ui_maker.saveState()


def load():
    global savedState
    ui_maker.restoreState(savedState)

param.child('save').sigActivated.connect(save)
param.child('load').sigActivated.connect(load)

param.sigTreeStateChanged.connect(updateChannels)

chanWidget = ui_maker.asWidget()
chanWidget.show()
win.addWidget(chanWidget)
win.show()