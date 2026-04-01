from enum import IntEnum
from typing import Dict, List
import numpy as np
from lookback import Lookback


class Channel(IntEnum):
    LEFT = 0
    RIGHT = 1
    MID = 2
    LSIDE = 3
    RSIDE = 4

MONO_MAPPING = {
    Channel.LEFT: 0,
    Channel.RIGHT: 0,
    Channel.MID: 0,
}

STEREO_MAPPING = {
    Channel.LEFT: 0,
    Channel.RIGHT: 1,
    Channel.MID: 2,
    Channel.LSIDE: 3,
    Channel.RSIDE: 4,
}

class ChannelError(Exception):
    pass

class ChannelManager:
    _lookback_duration_ms = 100

    def __init__(
        self,
        n_channels: int,
        sample_rate: int,
        hop_size: int,
    ):
        self._n_input_channels = n_channels
        self._sample_rate = sample_rate
        self._hop_size = hop_size
        self.inbuffers: List[np.ndarray] = []
        self._lookbacks: Dict[Channel, Lookback] = {}
        self._mapping: Dict[Channel, int]
        self._init_buffers()
        self._set_mapping()

    def _init_buffers(self):
        if self._n_input_channels == 1:
            self._inbuffers = [np.array([])]
            self._lookbacks = {
                Channel.MID: Lookback(self._lookback_duration_ms, self._sample_rate, self._hop_size)
            }
        elif self._n_input_channels == 2:
        # L R, MID LSIDE, RSIDE
            self._inbuffers = [
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
            ]
            self._lookbacks = {
                channel: Lookback(self._lookback_duration_ms, self._sample_rate, self._hop_size)
                for channel in Channel
            }
        else:
            raise ValueError(f"Unsupported number of input channels: {self._n_input_channels}")

    def get_buffer(self, channel: Channel) -> np.ndarray:
        if channel not in self._mapping:
            raise ChannelError(f"Unknown channel: {channel}")
        return self._inbuffers[self._mapping[channel]]


    def get_lookback(self, channel: Channel) -> Lookback:
        return self._lookbacks[channel]


    def get_lookbacks(self):
        return self._lookbacks


    def load_results(self, windows: Dict[Channel, np.ndarray], all_freqs: Dict[Channel, np.ndarray]):
        for channel in all_freqs:
            self._lookbacks[channel].push_results(windows[channel], all_freqs[channel])


    def load_frames(self, frames: List[np.ndarray]) -> None:
        if self._n_input_channels == 1:
            self._inbuffers[0] = np.concatenate((self._inbuffers[0], frames[0]))

        elif self._n_input_channels == 2:
            L = frames[0]
            R = frames[1]
            mid = (L + R) / 2
            lside = L - mid
            rside = R - mid
            self._inbuffers[0] = np.concatenate((self._inbuffers[0], L))
            self._inbuffers[1] = np.concatenate((self._inbuffers[1], R))
            self._inbuffers[2] = np.concatenate((self._inbuffers[2], mid))
            self._inbuffers[3] = np.concatenate((self._inbuffers[3], lside))
            self._inbuffers[4] = np.concatenate((self._inbuffers[4], rside))

    def pop_frames(self, window_size: int, hop_size: int) -> Dict[Channel, np.ndarray]:
        result = {}
        for i, buffer in enumerate(self._inbuffers):
            window = buffer[:window_size]
            result[Channel(i)] = (window)
            self._inbuffers[i] = buffer[hop_size:]
        return result

    def buffer_ready(self, window_size: int) -> bool:
        return len(self._inbuffers[0]) >= window_size


    def reset(self) -> None:
        self._inbuffers = [np.array([]) for _ in self._inbuffers]


    def _set_mapping(self):
        if self._n_input_channels == 1:
            self._mapping = MONO_MAPPING
        
        elif self._n_input_channels == 2:
            self._mapping = STEREO_MAPPING
