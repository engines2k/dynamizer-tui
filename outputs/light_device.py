from typing import List

from channelmanager import Channel
from .light_buffer import LightEffectBuffer, LightBufferFrame


class DeviceBuffer:
    def __init__(self, start: int, effect: LightEffectBuffer):
        self._start = start
        self.effect = effect

    @property
    def channel(self) -> Channel:
        return self.effect.channel

    @channel.setter
    def channel(self, value: Channel) -> None:
        self.effect.channel = value

    @property
    def start(self) -> int:
        return self._start

    @start.setter
    def start(self, value: int) -> None:
        self._start = value

    @property
    def end(self) -> int:
        return self.start + self.effect.length - 1

    @property
    def name(self) -> str:
        return self.effect.name

    @property
    def settings(self):
        return _BufferSettings(self)


class _BufferSettings:
    def __init__(self, device_buffer: DeviceBuffer):
        self._buffer = device_buffer

    def __getitem__(self, key: str):
        if key == "start":
            return self._buffer.start
        raise KeyError(key)

    def __setitem__(self, key: str, value) -> None:
        if key == "start":
            self._buffer.start = value
        else:
            raise KeyError(key)


class LightDevice():
    def __init__(self, led_count, buffers: List[DeviceBuffer]=[]):
        self.led_count = led_count
        self.buffers: List[DeviceBuffer] = buffers

    @property
    def n_leds(self):
        return self.led_count

    def set_n_leds(self, n_leds):
        self.led_count = n_leds

    def handle_signal(self, features, channel=None):
        for buffer in self.buffers:
            buffer.effect.handle_signal(features, buffer.channel)


    def build_payload(self):
        if self.buffers is None:
            return []
        result = LightBufferFrame([1] * (self.led_count * 3))
        for buffer in self.buffers:
            result = result.place(buffer.effect.frame, buffer.start)
        return result
