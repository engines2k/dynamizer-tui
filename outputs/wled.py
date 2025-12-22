#TODO: Go through and give everything a decent name
import socket
import time
from collections import deque

WLED_HOST = "wled-bfn.local"
WLED_PORT = 21324
LISTEN_TIMEOUT_SECONDS = 2

LIGHT_SETTINGS_KICK = {
    'multiplier': .3,
    'adjust': 0,
    'color': (1, 255, 255), #BRG
    'blend_amount': 6
}

LIGHT_SETTINGS_SNARE = {
    'multiplier': 1.5,
    'adjust': 0,
    'color': (100, 30, 15), #BRG
    'blend_amount': 6
}

class LightBuffer:
    def __init__(self, num_leds, settings):
        self.buffer = deque(maxlen=num_leds)
        self.settings = settings

    def _handle_signal(self, signal):
        intensity = self.calc_intensity(signal)
        blended_intensities = self._blend_signal(intensity)
        self.buffer.extendleft(blended_intensities)

    def _blend_signal(self, intensity):
        result = []
        prev_value = self.buffer[0] if len(self.buffer) > 0 else [1, 1, 1]
        target_value = [ min(intensity, channel) for channel in self.settings['color'] ]
        for i in range(self.settings['blend_amount']):
            blend = (i + 1) / self.settings['blend_amount']
            blended = [
                int(prev_value[j] * (1 - blend) + target_value[j] * blend)
                for j in range(3)
            ]
            result.append(blended)
        return result

    def _build_frame(self):
        buffer_list = list(self.buffer)
        num_items = min(len(buffer_list), 50)

        frame = buffer_list[:num_items]

        if num_items < 50:
            frame.extend([[0, 0, 0]] * (50 - num_items))

        frame.reverse()
        frame.extend(reversed(frame))

        flattened: list[int] = [ c for sublist in frame for c in sublist ]
        return flattened 

    def calc_intensity(self, signal):
        # Apply threshold/adjustment to remove noise
        adjusted_signal = max(signal + self.settings['adjust'], 0)

        # Scale: divide first (larger divisor = weaker signal), then square for non-linear response
        # multiplier works inversely here: smaller multiplier = divide by larger number = weaker
        divisor = int(125 / self.settings['multiplier']) if self.settings['multiplier'] > 0 else 125
        scaled = adjusted_signal // divisor
        intensity = scaled ** 2 + 1

        return intensity


class WLEDClient:
    def __init__(self):
        self.host = WLED_HOST
        self.port = WLED_PORT
        self._lights: list[LightBuffer] = [LightBuffer(num_leds=100, settings=LIGHT_SETTINGS_KICK), LightBuffer(num_leds=100, settings=LIGHT_SETTINGS_SNARE)]
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        
        self._max_send_rate_hz = 250
        self._min_send_interval = 1.0 / self._max_send_rate_hz
        self._last_send_time = 0

        self._resolve_address()

    def _resolve_address(self):
        try:
            self._resolved_address = (socket.gethostbyname(WLED_HOST), WLED_PORT)
        except socket.gaierror:
            self._resolved_address = (WLED_HOST, WLED_PORT)

    def _build_payload(self, signal1, signal2):
        payload = bytearray()
        payload.append(LISTEN_TIMEOUT_SECONDS)

        for light, signal in zip(self._lights, (signal1, signal2)):
            light._handle_signal(signal)
            payload += bytes(light._build_frame())

        return payload

    def send(self, signal1, signal2):
        if not self._ready_to_send:
            return

        payload = self._build_payload(signal1, signal2)

        try:
            self._socket.sendto(payload, self._resolved_address)
            self._last_send_time = time.time()
        except BlockingIOError:
            pass


    @property
    def _ready_to_send(self):
        current_time = time.time()
        if current_time - self._last_send_time < self._min_send_interval:
            return False
        return True

#buffer1 = deque(maxlen=num_leds)
#buffer2 = deque(maxlen=num_leds)

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.setblocking(False)


