import numpy as np
import scipy

from acq4.devices.PatchPipette.states import PatchPipetteState
from acq4.util import ptime


class ClearState(PatchPipetteState):
    """A cross between Break In and Seal that scans pressures for possible recovery of a cell loss.

    Parameters
    ----------
    recoveryTimeout : float
        Time (s) to spend trying to recover from a cell loss before giving up (default 30 s).
    recoveryResistanceThresholdAbsolute : float
        Access resistance (Ohms) below which to consider the cell loss successfully reversed and
        transition to 'whole cell' state (default 10 MΩ).
    recoverySustainedTime : float
        Time (s) that resistance must be below the recovery threshold before considering the cell loss successfully
        reversed and transitioning to 'whole cell' state (default 2 s).
    """

    stateName = 'clear'

    _parameterDefaultOverrides = {
        'initialPressureSource': 'atmosphere',
        'initialClampMode': 'VC',
        'initialVCHolding': -70e-3,
        'initialTestPulseEnable': True,
        'fallbackState': 'fouled',
    }
    _parameterTreeConfig = {
        'recoveryTimeout': {'type': 'float', 'default': 60.0, 'suffix': 's'},
        'recoveryResistanceThresholdAbsolute': {'type': 'float', 'default': 10e6, 'suffix': 'Ω', 'siPrefix': True},
        'recoverySustainedTime': {'type': 'float', 'default': 2.0, 'suffix': 's'},
    }

    def run(self):
        # TODO relative R_acc threshold?
        start = ptime.time()
        tps = []
        while start + 2 > ptime.time():
            tps.extend(self.processAtLeastOneTestPulse())
        best_r_acc = min(tp['access_resistance'] for tp in tps)
        pressure = -500  # Pa
        start = ptime.time()
        sign_has_flipped = False
        while start + self.config['recoveryTimeout'] > ptime.time():
            first_recovery_time = None
            while (
                self.processAtLeastOneTestPulse()[-1].analysis['access_resistance']
                < self.config['recoveryResistanceThresholdAbsolute']
            ):
                if first_recovery_time is None:
                    first_recovery_time = ptime.time()
                elif first_recovery_time + self.config['recoverySustainedTime'] < ptime.time():
                    self.setState("cell recovered")
                    # todo make sure when this lands in `main` we use the dict-style return
                    return "whole cell"

            pulse_start = ptime.time()
            tps_during = []
            self.waitFor(self.dev.pressureDevice.setPressure(pressure, source='regulator'))
            while pulse_start + 2 > ptime.time():
                tps_during.extend(self.processAtLeastOneTestPulse())
            self.dev.pressureDevice.setPressure(0, source='atmosphere')
            r_acc_during = np.asarray([tp['access_resistance'] for tp in tps_during])
            time_during = np.asarray([tp['event_time'] for tp in tps_during])
            slope = scipy.stats.linregress(r_acc_during, time_during).slope
            if slope < 0:
                tps_after = []
                while pulse_start + 2 > ptime.time():
                    tps_after.extend(self.processAtLeastOneTestPulse())
                r_acc_after = np.asarray([tp['access_resistance'] for tp in tps_after])
                if r_acc_after.mean() < best_r_acc:
                    best_r_acc = r_acc_after.mean()
                    # and repeat the same pressure
                else:
                    # increase the pressure magnitude
                    pressure = np.sign(pressure) * (abs(pressure) + 500)
            else:
                if sign_has_flipped:
                    # increase pressure magnitude and flip sign
                    pressure = -1 * np.sign(pressure) * (abs(pressure) + 500)
                else:
                    # first flip keeps magnitude the same
                    sign_has_flipped = True
                    pressure = -1 * pressure
        return self.config['fallbackState']
