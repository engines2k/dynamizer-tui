import pyaudio
import numpy as np
import threading
from typing import Dict, List, Callable, Optional
from dotenv import load_dotenv
from .abstractconnector import AbstractConnector

# Load environment variables (mirrors JACKConnector behavior)
load_dotenv()


class PAConnector(AbstractConnector):

    def __init__(self, process_callback: Callable):
        super().__init__()

        self.n_channels: int = 2
        self.active: bool = False
        self.input_is_aux: bool = False

        self._sample_rate: int = 44100
        self._buffer_size: int = 1024
        self._process_callback = process_callback
        self._pyaudio: pyaudio.PyAudio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._lock = threading.Lock()

        self._buffer_left: Optional[np.ndarray] = None
        self._buffer_right: Optional[np.ndarray] = None
        self._aux_boost: float = 0.15

        self._active_input: Optional[int] = None
        self._current_input_name: Optional[str] = None
        self._subscribers: List[Callable] = []
        self._audio_devices: Dict[str, int] = {}

    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def get_inputs(self) -> List[str]:
        self._audio_devices.clear()
        self._find_audio_devices()
        return list(self._audio_devices.keys())

    def switch_input(self, input: str) -> None:
        if input not in self._audio_devices:
            raise ValueError(f"Input device '{input}' not found")

        if self.active:
            was_active = True
            self._disconnect_input()
        else:
            was_active = False

        self._active_input = self._audio_devices[input]
        self._current_input_name = input
        self.input_is_aux = False
        self._apply_aux_boost()

        if was_active:
            self._connect_input()

        self._publish_input_switch()

    def activate(self) -> None:
        if not self._audio_devices:
            self.get_inputs()

        if self._active_input is None:
            if not self._audio_devices:
                raise RuntimeError("No audio input devices available")
            first_device_name = next(iter(self._audio_devices))
            self._active_input = self._audio_devices[first_device_name]
            self._current_input_name = first_device_name

        self._connect_input()
        self.active = True

    def deactivate(self) -> None:
        self._disconnect_input()
        self.active = False

    def _connect_input(self) -> None:
        if self._active_input is None:
            raise RuntimeError("No audio device selected")

        try:
            dev_info = self._pyaudio.get_device_info_by_index(self._active_input)
            channels = min(int(dev_info['maxInputChannels']), 2)
            self.n_channels = channels

            supported_rate = self._find_supported_sample_rate(
                self._active_input, channels, dev_info
            )

            self._buffer_left = np.zeros(self._buffer_size, dtype=np.float32)
            self._buffer_right = np.zeros(self._buffer_size, dtype=np.float32) if channels == 2 else None

            self._stream = self._pyaudio.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=supported_rate,
                input=True,
                input_device_index=self._active_input,
                frames_per_buffer=self._buffer_size,
                stream_callback=self._audio_callback
            )
            self._stream.start_stream()

        except Exception as e:
            raise RuntimeError(f"Failed to connect to audio device: {e}")

    def _find_supported_sample_rate(
        self, device_index: int, channels: int, dev_info: dict
    ) -> int:
        device_default = int(dev_info.get('defaultSampleRate', self._sample_rate))
        candidate_rates = [device_default, self._sample_rate, 48000, 44100, 32000]

        for rate in candidate_rates:
            try:
                if self._pyaudio.is_format_supported(
                    rate=rate,
                    input_device=device_index,
                    input_channels=channels,
                    input_format=pyaudio.paFloat32,
                ):
                    return rate
            except Exception:
                continue

        return device_default

    def _disconnect_input(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        self._buffer_left = None
        self._buffer_right = None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)

        if self._buffer_right is not None:
            self._buffer_left[:] = audio_data[::2]
            self._buffer_right[:] = audio_data[1::2]
        else:
            self._buffer_left[:] = audio_data

        self._process_callback(frame_count)
        return (None, pyaudio.paContinue)

    def _publish_input_switch(self) -> None:
        for callback in self._subscribers:
            callback()

    def get_buffers(self) -> List[np.ndarray]:
        if self._buffer_right is not None:
            return [self._buffer_left, self._buffer_right]
        return [self._buffer_left]

    def _find_audio_devices(self) -> None:
        wasapi_index = None
        for i in range(self._pyaudio.get_host_api_count()):
            api_info = self._pyaudio.get_host_api_info_by_index(i)
            if api_info['type'] == pyaudio.paWASAPI:
                wasapi_index = i
                break

        for i in range(self._pyaudio.get_device_count()):
            dev = self._pyaudio.get_device_info_by_index(i)
            if not self._is_device_usable(dev, wasapi_index):
                continue

            name = dev['name']
            is_loopback = dev.get('isLoopbackDevice', False)

            if is_loopback:
                self._audio_devices[f"{name} (Loopback)"] = i
            elif dev['maxInputChannels'] > 0 and dev['hostApi'] == wasapi_index:
                if 'loopback' in name.lower() or 'stereo mix' in name.lower():
                    self._audio_devices[f"{name} (WASAPI Loopback)"] = i
            elif dev['maxInputChannels'] > 0 and not is_loopback:
                if name not in self._audio_devices:
                    api_info = self._pyaudio.get_host_api_info_by_index(dev['hostApi'])
                    if api_info['name'] != 'MME':
                        name = f"{name} ({api_info['name']})"
                    self._audio_devices[name] = i

    def _is_device_usable(self, dev: dict, wasapi_index: Optional[int]) -> bool:
        if not dev.get('name') or not dev['name'].strip():
            return False
        if dev.get('defaultSampleRate', 0) <= 0:
            return False

        name_lower = dev['name'].lower()
        excluded = ['microsoft sound mapper', 'primary sound', 'communications device']
        if any(ex in name_lower for ex in excluded):
            return False

        if dev.get('isLoopbackDevice', False):
            return True

        if dev['hostApi'] == wasapi_index and dev['maxInputChannels'] > 0:
            return True

        if dev['maxInputChannels'] > 0:
            return True

        return False

    def _apply_aux_boost(self) -> None:
        if self.input_is_aux and self._buffer_left is not None:
            self._buffer_left *= self._aux_boost
            if self._buffer_right is not None:
                self._buffer_right *= self._aux_boost

    def __del__(self):
        try:
            self.deactivate()
        except Exception:
            pass
        try:
            if hasattr(self, '_pyaudio') and self._pyaudio:
                self._pyaudio.terminate()
        except Exception:
            pass
