from outputs.abstractvisualizer import AbstractVisualizer
from processors import AdaptiveThreshold

class AmplitudeVisualizer(AbstractVisualizer):

    def __init__(self, feature_key: str, output_width=40, channel: int = 0):
        self._threshold = AdaptiveThreshold(decay_rate=7, raise_factor=30, raise_type='FLAT')
        self._output_width = output_width
        self._key = feature_key
        self._channel = channel
        self.result = ''

    def activate(self):
        pass

    def send(self, features):
        channel_features = features.get(self._channel, {})
        signal = channel_features.get(self._key, 0)
        self._threshold.track(signal)
        ceiling = self._threshold.current + .00000000000001
        stars = ("*" * int((signal / ceiling) * self._output_width))
        empty = " " * (self._output_width - len(stars))
        self.result = f'{signal:4.0f}:{stars}{empty}|{ceiling:4.0f}'
        
        print(self.result)


class FrequencyVisualizer(AbstractVisualizer):

    def __init__(self, channel: int = 0):
        self._channel = channel

    def activate(self):
        pass

    def send(self, features):
        channel_features = features[self._channel]
        res = ""
        for i in range(0, len(features['freqs']), 2):
            strength = int(features['freqs'][i])
            if strength :
                res += f"{strength:1.0f} "
            else:
                res += " ."
            print(res)

