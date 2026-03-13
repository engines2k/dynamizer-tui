#TODO: Go through and give everything a decent name
import socket
import time
from .light_buffer import LightBuffer
from collections import deque

OUTPUT_DELAY = 0 #130
WLED_HOST = "wled-bfn.local"
WLED_PORT = 21324
LISTEN_TIMEOUT_SECONDS = 2

LIGHT_SETTINGS_LOW = {
    'multiplier': 0.3001, #.3
    'adjust': 0,
    'color': (2, 255, 255), #BRG
    'speed': 6
}

LIGHT_SETTINGS_LOW_BEAT = {
    'multiplier': .071,
    'adjust': 0,
    'color': (12, 255, 80), #BRG 
    'speed': 5
}

LIGHT_SETTINGS_HIGH = {
    'multiplier': 2,
    'adjust': 0,
    'color': (100, 30, 15), #BRG
    'speed': 6
}

class DelayQueueItem():
    def __init__(self, data):
        self.data = data
        self.created = time.time()*1000

class DelayQueue():
    def __init__(self, delay=0):
        self._delay = delay
        self._queue = deque()

    def push(self, item):
        self._queue.appendleft(DelayQueueItem(item))

    def get_ready_items(self):
        result = []
        current_time = time.time()*1000
        not_ready = deque()

        # Separate ready items from not-ready items
        while self._queue:
            item = self._queue.pop()
            item_ready_time = item.created + self._delay
            if item_ready_time <= current_time:
                result.append(item.data)
            else:
                not_ready.appendleft(item)

        # Put not-ready items back in the queue
        self._queue = not_ready
        return result

class WLEDClient:
    def __init__(self):
        self.multiplier = 1.3

        self.host = WLED_HOST
        self.port = WLED_PORT
        self._packet_queue = DelayQueue(delay=0)

        self._light_buffers: dict[str, LightBuffer] = {
            'low': LightBuffer(num_leds=50, settings=LIGHT_SETTINGS_LOW),
            'high': LightBuffer(num_leds=50, settings=LIGHT_SETTINGS_HIGH),
            'low_beat': LightBuffer(num_leds=50, settings=LIGHT_SETTINGS_LOW_BEAT)
        }
        
        self._max_send_rate_hz = 250
        self._min_send_interval = 1.0 / self._max_send_rate_hz
        self._last_send_time = 0

    def activate(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._resolve_address()

    def _resolve_address(self):
        try:
            self._resolved_address = (socket.gethostbyname(WLED_HOST), WLED_PORT)
        except socket.gaierror:
            self._resolved_address = (WLED_HOST, WLED_PORT)

    def _build_payload(self, signal1, signal2, kick_signal):

        payload = bytearray()
        payload.append(LISTEN_TIMEOUT_SECONDS)


        # Process signals into their respective buffers
        self._light_buffers['low']._handle_signal(signal1 * self.multiplier)  # Kick buffer
        self._light_buffers['high']._handle_signal(signal2 * self.multiplier)  # Snare buffer
        self._light_buffers['low_beat']._handle_signal(kick_signal * self.multiplier)  # Snare buffer

        low_frame = self._light_buffers['low'].frame
        high_frame = self._light_buffers['high'].frame
        kick_frame = self._light_buffers['low_beat'].frame

        low_combined = low_frame + kick_frame

        payload += bytes(low_combined)
        payload += bytes(high_frame)

        payload += bytes(low_combined)
        payload += bytes(high_frame)

        return payload

    def send(self, signal1, signal2, kick_signal):
        if not self._ready_to_send:
            return

        payload = self._build_payload(signal1, signal2, kick_signal**2)

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
        current_time = time.time()
        if current_time - self._last_send_time < self._min_send_interval:
            return False
        return True

