from typing import List, Tuple
from .light_buffer import LightEffectBuffer, LightBufferFrame

class LightDevice():
    def __init__(self, led_count, buffers: List[Tuple[int, LightEffectBuffer]]=[]):
        self.led_count = led_count
        self.buffers: List[Tuple[int, LightEffectBuffer]] = buffers

    @property
    def n_leds(self):
        return self.led_count

    def set_n_leds(self, n_leds):
        self.led_count = n_leds

    def handle_signal(self, features):
        for _, buffer in self.buffers:
            buffer.handle_signal(features)


    def build_payload(self):
        if self.buffers is None:
            return []
        result = LightBufferFrame([1] * (self.led_count * 3))
        for position, buffer in self.buffers:
            result = result.place(buffer.frame, position)
        return result
