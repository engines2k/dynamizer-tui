from collections import deque
from typing import List

class LightDevice():
    def __init__(self, n_leds, buffers: List[LightBuffer]=[]):
        self._n_leds = n_leds
        self._buffers: List[LightBuffer] = buffers

    @property
    def n_leds(self):
        return self._n_leds

    def set_n_leds(self, n_leds):
        self._n_leds = n_leds

    def build_payload(self):
        if self._buffers is None:
            return []
        result: LightBufferFrame = LightBufferFrame()
        for buffer in self._buffers:
            if not result:
                result = buffer.frame
            else:
                result = result + buffer.frame
        return result


class LightBufferFrame:
    def __init__(self, frame=[]):
        self._frame = frame

    def __getitem__(self, index):
        return self._frame[index]
        
    def __repr__(self):
        return f'LightBufferFrame({self._frame})'

    def __str__(self):
        return str(self._frame)

    def __bytes__(self):
        return bytes(self._frame)

    def __len__(self):
        return len(self._frame)

    def __add__(self, other):
        added = []
        i = 0

        while i < len(self) and i < len(other):
            tmp = self[i] + other[i] - 1
            tmp = max(min(tmp, 255), 0)
            added.append(tmp)
            i += 1
        if i < len(self):
            added.append(self[i:])
        if i < len(other):
            added.append(other[i:])

        return LightBufferFrame(added)

class LightBuffer:
    def __init__(self, n_frames, settings):
        self._n_frames = n_frames
        self.buffer = deque(maxlen=self._n_frames)
        self.settings = settings
        self.frame = LightBufferFrame()

    @property
    def size(self):
        return self._n_frames

    def set_size(self, n_frames: int):
        self._n_frames = n_frames
        self.buffer = deque(maxlen=self._n_frames)

    def handle_signal(self, signal):
        intensity = self.calc_intensity(signal)
        blended_intensities = self._blend_signal(intensity)
        self.buffer.extendleft(blended_intensities)
        self.frame = self._build_frame()

    def _blend_signal(self, intensity):
        result = []
        prev_value = self.buffer[0] if len(self.buffer) > 0 else [1, 1, 1]
        target_value = [ min(intensity, channel) for channel in self.settings['color'] ]
        for i in range(self.settings['speed']):
            blend = (i + 1) / self.settings['speed']
            blended = [
                max(0, min(255, int(prev_value[j] * (1 - blend) + target_value[j] * blend)))
                for j in range(3)
            ]
            result.append(blended)
        return result

    def _build_frame(self):
        """Build a frame with specified number of LEDs (default 50).
        Takes half the LEDs, mirrors them to create the full strip pattern."""
        buffer_list = list(self.buffer)
        half_leds = self._n_frames // 2
        num_items = min(len(buffer_list), half_leds)

        frame = buffer_list[:num_items]

        # Pad to half the strip length
        if num_items < half_leds:
            frame.extend([[0, 0, 0]] * (half_leds - num_items))

        # Mirror: reverse and extend to create full strip
        frame.reverse()
        frame.extend(reversed(frame))

        # Clamp all values to valid byte range [0, 255] before flattening
        flattened: list[int] = [ max(0, min(255, c)) for sublist in frame for c in sublist ]
        return LightBufferFrame(flattened)

    def calc_intensity(self, signal):
        # Apply threshold/adjustment to remove noise
        adjusted_signal = max(signal + self.settings['adjust'], 0)

        # Scale: divide first (larger divisor = weaker signal), then square for non-linear response
        # multiplier works inversely here: smaller multiplier = divide by larger number = weaker
        divisor = int(125 / self.settings['multiplier']) if self.settings['multiplier'] > 0 else 125
        scaled = adjusted_signal // divisor
        intensity = scaled ** 2 + 1

        return intensity


