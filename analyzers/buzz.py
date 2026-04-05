from .abstractanalyzer import AbstractAnalyzer
from typing import Dict
import numpy as np
from channelmanager import Channel
from lookback import Lookback
from sys import float_info

class BuzzAnalyzer(AbstractAnalyzer):
    """
    buzz: Measures harmonic content in the bass register.
    Finds the 2 loudest fundamentals below 400Hz and computes
    the ratio of harmonic energy (2nd-7th harmonics) to fundamental energy.
    """
    label: str
    feature_type: str

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str='') -> None:
        self._lookbacks = lookbacks
        self._label = label+'_' if label else label

    def analyze(self, bins: np.ndarray, freq: Dict[Channel, np.ndarray], time: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        eps = float_info.epsilon

        mid_freq_linear = 10 ** (freq[Channel.MID] / 20)

        low_mask = bins < 400
        low_bins = bins[low_mask]
        low_amps = mid_freq_linear[low_mask]

        top2_idx = np.argsort(low_amps)[-2:]
        fundamentals = low_bins[top2_idx]
        fundamental_amps = low_amps[top2_idx]

        harmonic_sum = 0.0
        for fund, fund_amp in zip(fundamentals, fundamental_amps):
            for h in range(3, 11, 2):
                harmonic_freq = fund * h
                harmonic_idx = np.argmin(np.abs(bins - harmonic_freq))
                harmonic_sum += mid_freq_linear[harmonic_idx]

        avg_amp = np.mean(mid_freq_linear)
        res = float((harmonic_sum / (np.sum(fundamental_amps) + eps)) * avg_amp)

        return { Channel.MID: {'buzz': res } }
