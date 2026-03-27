from abc import ABC, abstractmethod
from typing import Dict, List
from numpy import ndarray
from channelmanager import Channel
from lookback import Lookback

class AbstractAnalyzer(ABC):
    label: str
    channel: Channel

    @abstractmethod
    def __init__(self, lookbacks: List[Lookback], label):
        pass

    @abstractmethod
    def analyze(self, bins: ndarray, freqs: ndarray) -> Dict:
        """
        Conduct some analysis of signal features from the frequencies
        and bins, and return the resulting features labeled in a dict.
        """
        pass

