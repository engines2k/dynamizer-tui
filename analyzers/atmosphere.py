from typing import Dict
import numpy as np
from .abstractanalyzer import AbstractAnalyzer
from channelmanager import Channel
from lookback import Lookback
from processors import SignalFollower

class AtmosphereAnalyzer(AbstractAnalyzer):
    """
    atmosphere: A state feature calculated from stereo width
    and signal presence / air (so HFC) relative to average with absolute bounds and in-out easing.
    Intended to measure the wideness and immersive quality of the signal.
    """
    label: str
    feature_type: str

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str='', lower_hz: int=2000, upper_hz: int=10000) -> None:
        self._follower = SignalFollower(attack=1, decay=1)
        self._label = label+'_' if label else label
        self._lower_hz = lower_hz
        self._upper_hz = upper_hz
        pass

    def analyze(self, bins: np.ndarray, freq: Dict[Channel, np.ndarray], time: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        # grab LSIDE and RSIDE channel signals
        lside_signal = freq[Channel.LSIDE][(bins >= self._lower_hz) & (bins <= self._upper_hz)]
        rside_signal = freq[Channel.RSIDE][(bins >= self._lower_hz) & (bins <= self._upper_hz)]
        #TODO: apply cubic ease-in-out
        lsum = np.average(lside_signal)
        rsum = np.average(rside_signal)

        avg = (lsum + rsum) / 2 
        result = self._follower.track(avg)
        
        return { Channel.MID: { f'{self._label}atmosphere': result } }

