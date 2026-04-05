from abc import ABC, abstractmethod
from typing import Dict
from numpy import ndarray
from channelmanager import Channel
from lookback import Lookback

class AbstractAnalyzer(ABC):
    """
    Processes a musical signal into a number representing an
    immediate piece of musical information, aka a feature.
    """
    label: str
    feature_type: str

    @abstractmethod
    def __init__(self, lookbacks: Dict[Channel, Lookback], label: str) -> None:
        pass

    @abstractmethod
    def analyze(self, bins: ndarray, freq: Dict[Channel, ndarray], time: Dict[Channel, ndarray]) -> Dict[Channel, Dict[str, float]]:
        """
        Conduct some analysis of signal features from the frequencies
        and bins, and return the resulting features labeled in a dict.
        """
        pass

