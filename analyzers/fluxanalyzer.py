from typing import Dict
import numpy as np
from channelmanager import Channel
from lookback import Lookback
from .abstractanalyzer import AbstractAnalyzer

class FluxAnalyzer(AbstractAnalyzer):
    feature_type: str = 'EVENT'

    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str):
        self._lookbacks = lookbacks
        self._label = label

    def analyze(self, bins: np.ndarray, freqs: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        try:
            prev_freqs: Dict[Channel, np.ndarray] = { 
                c: l.get_by_ms(40)[1]
                for c, l in self._lookbacks.items()
            }
        except LookupError:
            return {
                Channel.LEFT: { 'flux': 0.0 },
                Channel.RIGHT: { 'flux': 0.0 },
                Channel.MID: { 'flux': 0.0 },
            }
        flux_l = self._window_flux(freqs[Channel.LEFT], prev_freqs[Channel.LEFT])
        flux_r = self._window_flux(freqs[Channel.RIGHT], prev_freqs[Channel.RIGHT])
        flux_m = (flux_l + flux_r) / 2
        return {
            Channel.LEFT: { 'flux': flux_l },
            Channel.RIGHT: { 'flux': flux_r },
            Channel.MID: { 'flux': flux_m },
        }

    def _window_flux(self, window: np.ndarray, prev: np.ndarray) -> float:
        prev_avg = np.average(prev, axis=0)
        clipped = np.maximum(np.subtract(window, prev_avg), 0)
        flux = np.sum(clipped)
        return flux
