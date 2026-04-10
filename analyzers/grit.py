from processors.adaptivethreshold import AdaptiveThreshold
from .abstractanalyzer import AbstractAnalyzer
from typing import Dict
import numpy as np
from channelmanager import Channel
from lookback import Lookback
from sys import float_info
from processors import SignalFollower

class GritAnalyzer(AbstractAnalyzer):
    """
    grit: Measures harmonic content in the bass register.
    Finds the 2 loudest fundamentals below 400Hz and computes
    the ratio of harmonic energy (2nd-7th harmonics) to fundamental energy.
    """
    label: str
    feature_type: str

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str='') -> None:
        self._lookbacks = lookbacks
        self._label = label+'_' if label else label
        self._follower = SignalFollower(attack=1.5, decay=1)
        self._ceiling = AdaptiveThreshold(decay=.1, start=25, floor=20)

    def analyze(self, bins: np.ndarray, freq: Dict[Channel, np.ndarray], time: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        eps = float_info.epsilon

        linear_freq = 10 ** (freq[Channel.MID] / 20)

        low_mask = bins < 400
        low_bins = bins[low_mask]
        low_amps = linear_freq[low_mask]

        top2_idx = np.argsort(low_amps)[-2:]
        fundamentals = low_bins[top2_idx]
        fundamental_amps = low_amps[top2_idx]

        harmonic_sum = 0.0
        for fund, fund_amp in zip(fundamentals, fundamental_amps):
            for h in [4,5,7,9,11,13,15]:
                harmonic_freq = fund * h
                harmonic_idx = np.argmin(np.abs(bins - harmonic_freq))
                harmonic_sum += min(linear_freq[harmonic_idx], (fund_amp / h))

        avg_amp = np.mean(linear_freq)
        grit = (harmonic_sum / (np.sum(fundamental_amps) + eps)) * avg_amp
        smoothed = self._follower.track(grit) / self._ceiling.value
        self._ceiling.track(smoothed)
        eased = ease_in_out_cubic(smoothed)
        

        return { Channel.MID: {'grit': float(eased) } }

def ease_in_out_cubic(x: float) -> float:
    if x < .5:
        return 4 * x * x * x
    return 1 - (-2 * x + 2)**3 / 2
