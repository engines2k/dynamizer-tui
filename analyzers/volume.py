import numpy as np
from typing import Dict
from channelmanager import Channel
from lookback import Lookback
from .abstractanalyzer import AbstractAnalyzer
from processors import SignalFollower, AdaptiveThreshold

class VolumeAnalyzer(AbstractAnalyzer):

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str = '') -> None:
        self._lookbacks = lookbacks
        self._label = label
        self._dynamic_ceil = AdaptiveThreshold(decay=.01, start=15, floor=15)
        self._smoother = SignalFollower(attack=30, decay=4)

    def analyze(self, bins: np.ndarray, freqs: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        # calc mid channel avg amplitude
        # follow with signal, high attack, slow-ish decay
        vol = np.average(freqs[Channel.LEFT])
        smoothed_vol = self._smoother.track(vol)
        self._dynamic_ceil.track(smoothed_vol)
        ceil = self._dynamic_ceil.current
        return {
            Channel.MID: { 'volume': smoothed_vol / ceil }
        }
