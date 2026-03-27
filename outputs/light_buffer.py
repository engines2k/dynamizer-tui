from collections import deque

from channelmanager import Channel

class LightEffectBuffer:
    def __init__(self, name: str, feature: str, length: int, settings: dict, channel: Channel = Channel.LEFT):
        self.name = name
        self.feature = feature
        self.length = length
        self.buffer = deque(maxlen=self.length)
        self.settings = settings
        self.frame = LightBufferFrame()
        self._channel = channel

    @property
    def channel(self) -> Channel:
        return self._channel

    @channel.setter
    def channel(self, value: Channel) -> None:
        if value < 0:
            print(f"Warning: LightEffectBuffer '{self.name}' requested channel {value} (negative). Ignoring.")
            return
        self._channel = value

    @property
    def size(self):
        return self.length

    def set_size(self, n_frames: int):
        self.length = n_frames
        self.buffer = deque(maxlen=self.length)

    def handle_signal(self, feature_value: float):
        intensity = self.calc_intensity(feature_value)
        blended_intensities = self._blend_signal(intensity)
        self.buffer.extendleft(blended_intensities)
        self.frame = self._build_frame()

    def _blend_signal(self, intensity: float):
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
        half_leds = self.length // 2
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
        divisor = 125 #TODO: ITS MAGIC!
        # Apply threshold/adjustment to remove noise
        adjusted_signal = max(signal + self.settings.get('adjust', 0), 1)
        adjusted_signal *= self.settings.get('multiplier', 1)

        scaled = adjusted_signal // divisor
        intensity = scaled ** 2 + 1 #for a peakier signal

        return intensity


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

