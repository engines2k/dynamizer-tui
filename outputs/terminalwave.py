from typing import Callable, List
from processors import AdaptiveThreshold
from .abstractvisualizer import AbstractVisualizer

class AmplitudeVisualizer(AbstractVisualizer):

    def __init__(self, feature_key: str, output_width=40, channel: int = 0):
        self._threshold = AdaptiveThreshold(decay_rate=1)
        self._output_width = output_width
        self._key = feature_key
        self._channel = channel
        self.result = ''
        self._callbacks: List[Callable] = []

    def subscribe(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def activate(self):
        pass

    def send(self, features):
        if isinstance(features, list):
            features = features[self._channel]
        signal = features[self._key]
        self._threshold.track(signal)
        ceiling = self._threshold.current + .00000000000001
        self.result = ("*" * int((signal / ceiling) * self._output_width))
        for callback in self._callbacks:
            callback(self.result)


class FrequencyVisualizer(AbstractVisualizer):

    def __init__(self, channel: int = 0):
        self._channel = channel

    def activate(self):
        pass

    def send(self, features):
        if isinstance(features, list):
            features = features[self._channel]
        res = ""
        for i in range(0, len(features['freqs']), 2):
            strength = int(features['freqs'][i])
            if strength > 25:
                res += f"{strength % 100:1.0f} "
            else:
                res += " ."
            print(res)

