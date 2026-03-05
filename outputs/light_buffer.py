from collections import deque
from typing import List, Tuple

class LightDevice():
    def __init__(self, n_leds, buffers: List[Tuple[int, LightBuffer]]=[]):
        self._n_leds = n_leds
        self._buffers: List[Tuple[int, LightBuffer]] = buffers

    @property
    def n_leds(self):
        return self._n_leds

    def set_n_leds(self, n_leds):
        self._n_leds = n_leds

    def build_payload(self):
        if self._buffers is None:
            return []
        result = LightBufferFrame([1] * (self._n_leds * 3))
        for position, buffer in self._buffers:
            result = result.place(buffer.frame, position)
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

    def __add__(self, other, offset=0):
        added = []
        i = 0
        offset *= 3 # R, G, B

        while i < len(self) and i+offset < len(other):
            tmp = self[i] + other[i+offset] - 1
            tmp = max(min(tmp, 255), 1)
            added.append(tmp)
            i += 1
        if i < len(self):
            added.extend(self[i:])
        if i+offset < len(other):
            added.extend(other[i+offset:])

        return LightBufferFrame(added)

    def place(self, other, led_offset=0, blend=True):
        offset = led_offset * 3
        result = list(self._frame)
        for i, val in enumerate(other._frame):
            pos = offset + i
            if pos < len(result):
                if blend:
                    result[pos] = max(1, min(255, result[pos] + val - 1))
                else:
                    result[pos] = max(1, min(255, val))
        return LightBufferFrame(result)

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
        multiplier = self.settings.get('multiplier', 1.0)
        target_value = [ min(intensity, int(channel * multiplier)) for channel in self.settings['color'] ]
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
            frame.extend([[1, 1, 1]] * (half_leds - num_items))

        # Mirror: reverse and extend to create full strip
        frame.reverse()
        frame.extend(reversed(frame))

        # Clamp all values to valid byte range [0, 255] before flattening
        flattened: list[int] = [ max(1, min(255, c)) for sublist in frame for c in sublist ]
        return LightBufferFrame(flattened)

    def calc_intensity(self, signal):
        # Apply threshold/adjustment to remove noise
        adjusted_signal = max(signal + self.settings['adjust'], 1)

        # Scale: divide first (larger divisor = weaker signal), then square for non-linear response
        # multiplier works inversely here: smaller multiplier = divide by larger number = weaker
        divisor = int(125 / self.settings['multiplier']) if self.settings['multiplier'] > 1 else 125
        scaled = adjusted_signal // divisor
        intensity = scaled ** 2 + 1

        return intensity


