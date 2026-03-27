from enum import IntEnum
from typing import List
import numpy as np
from lookback import Lookback


class Channel(IntEnum):
    MID = 0
    LEFT = 1
    RIGHT = 2
    LSIDE = 3
    RSIDE = 4


class ChannelError(Exception):
    pass

class ChannelManager:
    def __init__(
        self,
        n_channels: int,
        sample_rate: int,
        hop_size: int,
        lookback_duration_ms: int
    ):
        self._n_input_channels = n_channels
        self._sample_rate = sample_rate
        self._hop_size = hop_size
        self._lookback_duration_ms = lookback_duration_ms
        self.inbuffers: List[np.ndarray] = []
        self.lookbacks: List[Lookback] = []
        self._init_buffers()

    def _init_buffers(self):
        if self._n_input_channels == 1:
            self._inbuffers = [np.array([])]
            self._lookbacks = [
                Lookback(self._lookback_duration_ms, self._sample_rate, self._hop_size)
            ]
        elif self._n_input_channels == 2:
        # L R, MID LSIDE, RSIDE
            self._inbuffers = [
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
                np.array([]),
            ]
            self._lookbacks = [
                Lookback(self._lookback_duration_ms, self._sample_rate, self._hop_size)
                for _ in range(5)
            ]
        else:
            raise ValueError(f"Unsupported number of input channels: {self._n_input_channels}")

    def get_buffer(self, channel: Channel) -> np.ndarray:
        if self._n_input_channels == 1:
            if channel in (Channel.MID, Channel.LEFT, Channel.RIGHT):
                return self._inbuffers[0]
            raise ChannelError(f"Channel {channel.name} not available for mono input")
        
        elif self._n_input_channels == 2:
            buffer_map = {
                Channel.LEFT: 0,
                Channel.RIGHT: 1,
                Channel.MID: 2,
                Channel.LSIDE: 3,
                Channel.RSIDE: 4,
            }
            if channel not in buffer_map:
                raise ChannelError(f"Unknown channel: {channel}")
            return self._inbuffers[buffer_map[channel]]
        
        raise ChannelError(f"No buffers available for {self._n_input_channels} input channels")

    def get_lookback(self, channel: Channel) -> Lookback:
        if self._n_input_channels == 1:
            if channel in (Channel.MID, Channel.LEFT, Channel.RIGHT):
                return self._lookbacks[0]
            raise ChannelError(f"Channel {channel.name} not available for mono input")
        
        elif self._n_input_channels == 2:
            lookback_map = {
                Channel.LEFT: 0,
                Channel.RIGHT: 1,
                Channel.MID: 2,
                Channel.LSIDE: 3,
                Channel.RSIDE: 4,
            }
            if channel not in lookback_map:
                raise ChannelError(f"Unknown channel: {channel}")
            return self._lookbacks[lookback_map[channel]]
        
        raise ChannelError(f"No lookbacks available for {self._n_input_channels} input channels")

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

    def pop_window(self, window_size: int, hop_size: int) -> List[np.ndarray]:
        result = []
        for i, buffer in enumerate(self._inbuffers):
            window = buffer[:window_size]
            result.append(window)
            self._inbuffers[i] = buffer[hop_size:]
        return result

    def buffer_ready(self, window_size: int) -> bool:
        return len(self._inbuffers[0]) >= window_size

    def reset(self) -> None:
        self._init_buffers()
