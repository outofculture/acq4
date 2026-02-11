from __future__ import annotations

from acq4.util import ptime
from ._base import PatchPipetteState


class WholeCellState(PatchPipetteState):
    """State representing a successful break-in, with the pipette dialed in for whole-cell recording.

    Parameters
    ----------
    cellLossResistanceThreshold : float
        If the pipette resistance rises above baseline plus this threshold (Ω), transition to
        `cellLossState` (default 20 MΩ).
    cellLossState : str
        Name of state to transition to if possible cell loss is detected (default 'clear').
    cellLossSustainedTime : float
        Time (s) that resistance must be above threshold before transitioning to `cellLossState`
        (default 2 s).
    """
    stateName = 'whole cell'
    _parameterDefaultOverrides = {
        'initialPressureSource': 'atmosphere',
        'initialClampMode': 'VC',
        'initialVCHolding': -70e-3,
        'initialTestPulseEnable': True,
        'initialAutoBiasEnable': True,
        'initialAutoBiasTarget': -70e-3,
    }
    _parameterTreeConfig = {
        'cellLossResistanceThreshold': {'type': 'float', 'value': 20e6, 'suffix': 'Ω', 'siPrefix': True, 'step': 1e6},
        'cellLossState': {'type': 'str', 'value': 'clear'},
        'cellLossSustainedTime': {'type': 'float', 'value': 2.0, 'suffix': 's', 'step': 0.5},
    }

    def run(self):
        patchrec = self.dev.patchRecord()
        patchrec['wholeCellStartTime'] = ptime.time()
        patchrec['wholeCellPosition'] = tuple(self.dev.pipetteDevice.globalPosition())

        # TODO: Option to switch to I=0 for a few seconds to get initial RMP decay

        tps = []
        start = ptime.time()
        while start + 5 > ptime.time():
            tps.extend(self.processAtLeastOneTestPulse())

        baseline_rss = sum(tp['steady_state_resistance'] for tp in tps) / len(tps)
        threshold = baseline_rss + self.config['cellLossResistanceThreshold']
        first_loss_time = None
        while True:
            tps = self.processAtLeastOneTestPulse()
            rss = tps[-1]['steady_state_resistance']
            if rss > threshold:
                if first_loss_time is None:
                    first_loss_time = ptime.time()
                elif first_loss_time + self.config['cellLossSustainedTime'] < ptime.time():
                    self.setState(f"cell loss in progress (resistance rose to {rss / 1e6:.1f} MΩ)")
                    # TODO make sure when this lands in `main` we use the dict-style return
                    return "clear"
            else:
                first_loss_time = None
            self.sleep(0.1)

    def cleanup(self):
        patchrec = self.dev.patchRecord()
        patchrec['wholeCellStopTime'] = ptime.time()
        return super().cleanup()
