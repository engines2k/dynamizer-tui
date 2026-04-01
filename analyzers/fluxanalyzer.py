from typing import Dict
import numpy as np
from channelmanager import Channel
from lookback import Lookback
from .abstractanalyzer import AbstractAnalyzer
from processors import AdaptiveThreshold, SignalFollower

class FluxAnalyzer(AbstractAnalyzer):
    feature_type: str = 'EVENT'
    lookback_duration = 100

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str):
        self._lookbacks = lookbacks
        self._label = label
        self._threshold = AdaptiveThreshold(start=3000, decay_rate=13, raise_factor=200, raise_type='FLAT', debouce_ms=1000)
        self._follower = SignalFollower(attack=1000, decay=5)

    def analyze(self, bins: np.ndarray, freqs: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        try:
            prev_freqs: Dict[Channel, np.ndarray] = { 
                c: l.get_by_ms(self.lookback_duration)[1]
                for c, l in self._lookbacks.items()
            }
        except LookupError:
            return {
                Channel.LEFT: { 'flux': 0.0 },
                Channel.RIGHT: { 'flux': 0.0 },
                Channel.MID: { 'flux': 0.0 },
            }
        flux_l = self._window_flux(bins, freqs[Channel.LEFT], prev_freqs[Channel.LEFT])
        flux_r = self._window_flux(bins, freqs[Channel.RIGHT], prev_freqs[Channel.RIGHT])
        flux_m = (flux_l + flux_r) / 2 

        self._threshold.track(flux_m)

        flux_m = max(0, flux_m -  self._threshold.current)
        self._follower.track(flux_m)
        flux_m = self._follower.value

        return {
            Channel.LEFT: { 'flux': flux_l },
            Channel.RIGHT: { 'flux': flux_r },
            Channel.MID: { 'flux': flux_m },
        }

    def _window_flux(self, bins, window: np.ndarray, prev: np.ndarray) -> float:
        prev_avg = np.average(prev, axis=0)
        clipped = np.maximum(np.subtract(window, prev_avg), 0)
        flux = np.sum(clipped)
        return flux
