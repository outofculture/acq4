from acq4.devices.PatchPipette.states import PatchPipetteState
from acq4.util import ptime


class ClearState(PatchPipetteState):
    """A cross between Break In and Seal that scans pressures for possible recovery of a cell loss.

    Parameters
    ----------
    """

    stateName = 'clear'

    _parameterDefaultOverrides = {
        'initialPressureSource': 'atmosphere',
        'initialClampMode': 'VC',
        'initialVCHolding': -70e-3,
        'initialTestPulseEnable': True,
    }
    _parameterTreeConfig = {}

    def run(self):
        start = ptime.time()
        tps = []
        while start + 2 > ptime.time():
            tps.extend(self.processAtLeastOneTestPulse())
        baseline_rss = sum(tp['steady_state_resistance'] for tp in tps) / len(tps)
        # Test both positive and negative pulses to see what is the effect on access resistance. E.g.:
        #     -500 Pa pulse for 2 seconds, reading test pulses during this time
        #     If effect was good + permanent, repeat
        #     If effect was good but went away after releasing pressure, try -1 kPa
        #     If effect was bad, try +500 Pa
        #     etc..
