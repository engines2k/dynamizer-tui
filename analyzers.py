from lookback import Lookback
from thresholds import AdaptiveThreshold

class BeatHarmonySeparator():
    def __init__(self, signal_lookback: Lookback, min_freq=0, max_freq=20000, label='signal'):
        self._label = label
        self._transient_threshold = AdaptiveThreshold(decay_rate=500, raise_factor=.4)
        self._signal_lookback = signal_lookback
        self._min_freq = min_freq
        self._max_freq = max_freq

    def analyze(self, bins, freqs):
        freqs = freqs[(bins > self._min_freq) & (bins < self._max_freq + 1)]
        signal = sum(freqs)

        self._transient_threshold.track(signal)
        threshold = int(self._transient_threshold.current)
        signal_beat = int(max(signal - threshold, 0))
        signal_harmony = int(min(signal, threshold))

        return {
            f'{self._label}_beat': signal_beat,
            f'{self._label}_harmony': signal_harmony
        }
