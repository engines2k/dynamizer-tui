from collections import deque
from itertools import islice
import math
import numpy as np

class Lookback():
    def __init__(self, duration_ms, sample_rate, hop_size):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self._buffer = deque(maxlen=self._ms_to_buffer_items(duration_ms))

    def push(self, item):
        self._buffer.appendleft(item)

    def get_by_ms(self, ms):
        num_items = self._ms_to_buffer_items(ms)
        if num_items > len(self._buffer):
            raise LookupError(f"Lookback duration of {ms} out of range")
        return np.array([item for item in islice(self._buffer, 0, num_items)])

    def _ms_to_buffer_items(self, ms):
        target_n_samples = self.sample_rate * ( ms / 1000 )
        target_frames = math.ceil(target_n_samples / self.hop_size)
        return target_frames

    def __getitem__(self, index):
        return self._buffer[index]

    def __len__(self):
        return self._buffer

    def __repr__(self):
        return f"Lookback(sample_rate={self.sample_rate} hop_size={self.hop_size} _buffer={self._buffer.__str__})"
