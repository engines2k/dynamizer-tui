import json
import socket
import time
from .light_buffer import LightEffectBuffer
from .light_device import LightDevice, DeviceBuffer
from .delayqueue import DelayQueue
from typing import Dict, List, Tuple

OUTPUT_DELAY = 0#220
LISTEN_TIMEOUT_SECONDS = 2


class WLEDClient:
    def __init__(self):
        self.multiplier = 1.3 #TODO: MAGIC!
        self.effects: List[LightEffectBuffer] = []
        self.controllers: List[WLEDController] = []
        self._sockets = List[socket.SocketIO]
        self._packet_queue = DelayQueue(delay=OUTPUT_DELAY)
        self._active = False
        self._max_send_rate_hz = 250
        self._min_send_interval = 1.0 / self._max_send_rate_hz
        self._last_send_time = 0
        self.load_from_file('wledconfig.json')


    def load_from_file(self, filepath: str):
        with open(filepath, 'r') as in_file:
            config = json.load(in_file)
        self.effect_lookup = {}
        for buffer_config in config['preset_buffers']:
            effect = LightEffectBuffer(**buffer_config)
            self.effects.append(effect)
            self.effect_lookup[effect.name] = effect
        for c_config in config['controllers']:
            controller = self._load_controller_config(c_config)
            self.controllers.append(controller)

    def _load_controller_config(self, config: dict) -> WLEDController:
        return WLEDController(
            name=config['name'],
            destinations=config['destinations'],
            devices=[ self._load_device_config(c) for c in config['devices'] ]
        )

    def _load_device_config(self, config: dict) -> LightDevice:
        buffers = []
        for buffer_config in config['buffers']:
            buffer_type = buffer_config['type']
            effect = None
            if buffer_type == 'preset':
                effect = self.effect_lookup[buffer_config['effect']]
            elif buffer_type == 'custom':
                effect = LightEffectBuffer(**buffer_config['settings'])
            else:
                raise Exception(f'buffer type {buffer_type} invalid, must be "preset" or "custom"!')
            buffers.append(DeviceBuffer(buffer_config['offset'], effect))

        return LightDevice(
            led_count=config['led_count'],
            buffers=buffers
        )


    def activate(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        for device in self.controllers:
            device.activate()
        self._active = True


    def send(self, features):
        if not self._ready_to_send:
            return

        for device in self.controllers:
            payload = device.build_payload(features)
            self._packet_queue.push(payload, device.resolved_addresses)
            ready_payloads = self._packet_queue.get_ready_items()
            for payload in ready_payloads:
                try:
                    for address in payload.addresses:
                        self._socket.sendto(payload.data, address)
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

class WLEDController():
    multiplier = 1.3 #TODO: MAGIC!

    def __init__(self,
                 name: str,
                 destinations: List[Dict],
                 devices: List[LightDevice]):
        self.name: str = name
        self.destinations: List[Dict] = destinations or []
        self.devices: List[LightDevice] = devices
        self.resolved_addresses: List[Tuple[str, str]]


    def activate(self):
        self._resolve_addresses()

    def build_payload(self, features):
        payload = bytearray()
        payload.append(LISTEN_TIMEOUT_SECONDS)

        for device in self.devices:
            for buffer in device.buffers:
                feature_value = features[buffer.effect.feature] * self.multiplier
                buffer.effect.handle_signal(feature_value)

        for device in self.devices:
            payload += bytes(device.build_payload())

        return payload

    def _resolve_addresses(self):
        self.resolved_addresses = []
        for dest in self.destinations:
            self.resolved_addresses.append((socket.gethostbyname(dest['host']), dest['port']))

