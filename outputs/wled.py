import socket
import time
from .light_buffer import LightBuffer, LightDevice
from .delayqueue import DelayQueue
from typing import List

OUTPUT_DELAY = 0#220
WLED_HOST = "4.3.2.1"
WLED_PORT = 21324
LISTEN_TIMEOUT_SECONDS = 2

LIGHT_SETTINGS_LOW = {
    'adjust': -1300,
    'multiplier': .5,
    'color': (5, 255, 118), #BRG
    'speed': 8
}

LIGHT_SETTINGS_LOW_BEAT = {
    'multiplier': .071,
    'adjust': 0,
    'color': (255, 255, 255), #BRG 
    'speed': 8
}

LIGHT_SETTINGS_HIGH = {
    'multiplier': 1,
    'adjust': 0,
    'color': (100, 30, 15), #BRG
    'speed': 6
}

class WLEDClient:
    def __init__(self):
        self.multiplier = 1.3
        self.host = WLED_HOST
        self.port = WLED_PORT
        self._packet_queue = DelayQueue(delay=OUTPUT_DELAY)
        self._active = False
        self._light_buffers: dict[str, LightBuffer] = {
            'kick_harmony': LightBuffer(n_frames=110, settings=LIGHT_SETTINGS_LOW),
            'kick_beat': LightBuffer(n_frames=110, settings=LIGHT_SETTINGS_LOW_BEAT),
            'snare_signal': LightBuffer(n_frames=30, settings=LIGHT_SETTINGS_HIGH),
        }

        self.light_devices: List[LightDevice] = [
            LightDevice(
                n_leds=144,
                buffers=[
                    (0, self._light_buffers['kick_harmony']),
                    (0, self._light_buffers['kick_beat']),
                    (113, self._light_buffers['snare_signal']),
                ]
            ),
            LightDevice(
                n_leds=144,
                buffers=[
                    (0, self._light_buffers['kick_harmony']),
                    (0, self._light_buffers['kick_beat']),
                    (113, self._light_buffers['snare_signal']),
                ]
            )
        ]
        self._max_send_rate_hz = 250
        self._min_send_interval = 1.0 / self._max_send_rate_hz
        self._last_send_time = 0

    def activate(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._resolve_address()
        self._active = True

    def _resolve_address(self):
        try:
            self._resolved_address = (socket.gethostbyname(WLED_HOST), WLED_PORT)
        except socket.gaierror:
            self._resolved_address = (WLED_HOST, WLED_PORT)

    def _build_payload(self, features):
        payload = bytearray()
        payload.append(LISTEN_TIMEOUT_SECONDS)

        for key, buffer in self._light_buffers.items():
            buffer.handle_signal(features[key] * self.multiplier)

        for device in self.light_devices:
            payload += bytes(device.build_payload())

        return payload

    def send(self, features):
        if not self._ready_to_send:
            return

        payload = self._build_payload(features)

        self._packet_queue.push(payload)

        ready_payloads = self._packet_queue.get_ready_items()

        for payload in ready_payloads:
            try:
                self._socket.sendto(payload, self._resolved_address)
                self._last_send_time = time.time()
            except BlockingIOError:
                pass


    @property
    def _ready_to_send(self):
        if not self._active:
            return False
        current_time = time.time()
        if current_time - self._last_send_time < self._min_send_interval:
            return False
        return True

