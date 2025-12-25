from lookback import Lookback
from processors import AdaptiveThreshold, SignalFollower

class BeatHarmonySeparator():
    def __init__(self, 
                 signal_lookback: Lookback,
                 floor=0,
                 min_freq=0,
                 max_freq=20000,
                 label='signal',
                 beat_attack=None,
                 beat_decay=None):

        self._label = label
        self._transient_threshold = AdaptiveThreshold(decay_rate=500, raise_factor=.4)
        self._signal_lookback = signal_lookback
        self._min_freq = min_freq
        self._max_freq = max_freq
        self._floor = floor

        if beat_attack != None or beat_decay != None:
            self._signal_follower = SignalFollower(attack=beat_attack, decay=beat_decay)
        else:
            self._signal_follower = None

    def analyze(self, bins, freqs):
        freqs = freqs[(bins > self._min_freq) & (bins < self._max_freq + 1)]
        signal = sum(freqs)

        self._transient_threshold.track(signal)
        threshold = int(self._transient_threshold.current)

        signal_beat = int(max(signal - threshold, 0))
        signal_beat = signal_beat if signal > self._floor else 0
        if self._signal_follower:
            signal_beat = int(self._signal_follower.track(signal_beat))

        signal_harmony = int(min(signal, threshold))

        return {
            f'{self._label}_signal': int(signal),
            f'{self._label}_beat': signal_beat,
            f'{self._label}_harmony': signal_harmony
        }
