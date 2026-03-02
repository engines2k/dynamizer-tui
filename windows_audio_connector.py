import os
import sounddevice as sd
import numpy as np
from dotenv import load_dotenv

__all__ = ["AudioConnector"]

load_dotenv()


class _Inport:
    def __init__(self, name: str, array: np.ndarray):
        self.name = name
        self._array = array

    def get_array(self) -> np.ndarray:
        return self._array


class AudioConnector():
    def __init__(self, process_callback) -> None:
        self._process_callback = process_callback
        self._stream: sd.InputStream | None = None
        self._active = False
        self._input = os.getenv('DEFAULT_INPUT') or ""
        self._inport_left = _Inport("left", np.array([]))
        self._inport_right = _Inport("right", np.array([]))
        self._left_buffer = np.array([])
        self._right_buffer = np.array([])
        self._device_id = None

    @staticmethod
    def shutdown_callback(status, reason):
        print("Audio shutdown:", status, reason)

    @property
    def available_ports(self):
        devices = sd.query_devices()
        if isinstance(devices, dict):
            devices = [devices]
        ports = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                ports.append(_DevicePort(i, dev['name'], dev['max_input_channels']))
        return ports

    def _get_device_id_from_input(self, input_name: str) -> int | None:
        devices = sd.query_devices()
        if isinstance(devices, dict):
            devices = [devices]
        for i, dev in enumerate(devices):
            if input_name in dev['name'] and dev['max_input_channels'] > 0:
                return i
        return None

    def activate(self):
        self._device_id = self._get_device_id_from_input(self._input) if self._input else None
        if self._device_id is None:
            default_input = sd.query_devices(kind='input')
            self._device_id = default_input['default_input_device']
        
        self._stream = sd.InputStream(
            device=self._device_id,
            channels=2,
            samplerate=44100,
            callback=self._audio_callback,
            blocksize=1024
        )
        self._stream.start()
        self._active = True

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags):
        self._left_buffer = np.concatenate((self._left_buffer, indata[:, 0]))
        self._right_buffer = np.concatenate((self._right_buffer, indata[:, 1]))
        
        self._inport_left = _Inport("left", self._left_buffer[:self._stream.blocksize * 10])
        self._inport_right = _Inport("right", self._right_buffer[:self._stream.blocksize * 10])
        
        if self._process_callback:
            self._process_callback(frames)

    def _connect_input(self):
        pass

    def set_input(self, input: str):
        was_active = self._active
        if self._active:
            self.deactivate()
        self._input = input
        if was_active:
            self.activate()

    def change_input(self, input: str):
        self.set_input(input)

    def _disconnect_input(self):
        pass

    def deactivate(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._active = False
        self._left_buffer = np.array([])
        self._right_buffer = np.array([])

    @property
    def inports(self):
        return [self._inport_left, self._inport_right]


class _DevicePort:
    def __init__(self, device_id: int, name: str, channels: int):
        self.device_id = device_id
        self.name = name
        self.channels = channels
