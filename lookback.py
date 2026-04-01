from collections import deque
from itertools import islice
import math
from typing import Deque, List, Tuple
import numpy as np

class Lookback():
    def __init__(self, duration_ms: int, sample_rate: int, hop_size: int):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self._time: Deque[np.ndarray] = deque(maxlen=self._ms_to_buffer_items(duration_ms))
        self._frequency: Deque[np.ndarray] = deque(maxlen=self._ms_to_buffer_items(duration_ms))

    def push_results(self, window: np.ndarray, freqs: np.ndarray):
        self._time.appendleft(window)
        self._frequency.appendleft(freqs)


    def get_by_ms(self, ms) -> Tuple[np.ndarray, np.ndarray]:
        num_items = self._ms_to_buffer_items(ms)
        if num_items > len(self._time):
            raise LookupError(f"Lookback duration of {ms} out of range")
        signal = np.array([item for item in islice(self._time, 0, num_items)])
        freqs = np.array([item for item in islice(self._frequency, 0, num_items)])
        return signal, freqs

    def _ms_to_buffer_items(self, ms) -> int:
        target_n_samples = self.sample_rate * ( ms / 1000 )
        target_frames = math.ceil(target_n_samples / self.hop_size)
        return target_frames

    def __getitem__(self, index):
        return self._time[index]

    def __len__(self) -> int:
        return len(self._time)

    def __repr__(self):
        return f"Lookback(sample_rate={self.sample_rate} hop_size={self.hop_size} _buffer={self._time.__str__})"
