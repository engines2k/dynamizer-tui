from abc import ABC, abstractmethod
from typing import Dict
from numpy import ndarray
from lookback import Lookback

class AbstractAnalyzer(ABC):
    label: str

    @abstractmethod
    def __init__(self, signal_lookback: Lookback, label):
        pass

    @abstractmethod
    def analyze(self, bins: ndarray, freqs: ndarray) -> Dict:
        """
        Conduct some analysis of signal features from the frequencies
        and bins, and return the resulting features labeled in a dict.
        """
        pass

