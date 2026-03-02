from abc import ABC, abstractmethod

class AbstractAnalyzer(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def activate(self):
        """Ready the analyzer for use."""
        pass

    @abstractmethod
    def send(self, features):
        """Receive and process signal features from analyzer."""
        pass
