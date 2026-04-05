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
        self._dynamic_ceil = AdaptiveThreshold(decay=.01, start=20, floor=20)
        self._smoother = SignalFollower(attack=30, decay=4)

    def analyze(self, bins: np.ndarray, freq: Dict[Channel, np.ndarray], time: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        # calc mid channel avg amplitude
        # follow with signal, high attack, slow-ish decay
        vol = np.average(freq[Channel.LEFT])
        smoothed_vol = self._smoother.track(vol)
        self._dynamic_ceil.track(smoothed_vol)
        ceil = self._dynamic_ceil.value
        return {
            Channel.MID: { 'volume': smoothed_vol / ceil }
        }
