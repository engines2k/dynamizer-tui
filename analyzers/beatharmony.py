from typing import Dict, List, Optional

from numpy import ndarray
from channelmanager import Channel
from lookback import Lookback
from processors import AdaptiveThreshold, SignalFollower
from .abstractanalyzer import AbstractAnalyzer

class BeatHarmonyAnalyzer(AbstractAnalyzer):
    def __init__(self,
                 lookbacks: Dict[Channel, Lookback],
                 channel: Channel,
                 label: str,
                 floor: int = 0,
                 mult: float = 1,
                 min_freq: int = 0,
                 max_freq: int = 20000,
                 beat_attack: Optional[float] = None,
                 beat_decay: Optional[float] = None):

        self.channel = channel
        self._label = label
        self._transient_threshold = AdaptiveThreshold(decay=500, raise_factor=.4)
        self._min_freq = min_freq
        self._max_freq = max_freq
        self._floor = floor
        self._mult = mult

        if beat_attack != None or beat_decay != None:
            self._signal_follower = SignalFollower(attack=beat_attack, decay=beat_decay)
        else:
            self._signal_follower = None

    def analyze(self, bins, freq: Dict[Channel, ndarray], time: Dict[Channel, ndarray]) -> Dict[Channel, Dict[str, float]]:
        channel_freqs = freq[self.channel][(bins > self._min_freq) & (bins < self._max_freq + 1)]
        signal = sum(channel_freqs) * self._mult

        self._transient_threshold.track(signal)
        threshold = int(self._transient_threshold.value)

        signal_beat = int(max(signal - threshold, 0))
        signal_beat = signal_beat if signal > self._floor else 0
        if self._signal_follower:
            signal_beat = int(self._signal_follower.track(signal_beat))

        signal_harmony = int(min(signal, threshold))

        return { self.channel: 
            {
                f'{self._label}_signal': int(signal),
                f'{self._label}_beat': signal_beat,
                f'{self._label}_harmony': signal_harmony
            }
        }
