from lookback import Lookback
from thresholds import AdaptiveThreshold
import numpy as np

class BeatHarmonySeparator():
    def __init__(self, signal_lookback: Lookback):
        self._transient_threshold = AdaptiveThreshold(decay_rate=500, raise_factor=.4)
        self._signal_lookback = signal_lookback

    def analyze(self, signal):
        self._transient_threshold.track(signal)
        threshold = int(self._transient_threshold.current)
        signal_beat = int(max(signal - threshold, 0))
        signal_harmony = int(min(signal, threshold))
        print(f'\nsignal:{signal}\nthreshold value: {threshold}\nbeat amplitude: {signal_beat}\nbeat harmony amplitude: {signal_harmony}')
