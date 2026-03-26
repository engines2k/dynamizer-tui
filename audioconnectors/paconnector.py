import pyaudiowpatch as pyaudio
import numpy as np
import threading
from typing import Dict, List, Callable, Optional
from .abstractconnector import AbstractConnector


class PAConnector(AbstractConnector):
    
    def __init__(self, process_callback: Callable):
        super().__init__()
        
        self.n_channels = 2
        self.active = False
        self.input_is_aux = False

        self._sample_rate = 44100
        self._buffer_size = 1024
        self._process_callback = process_callback
        self._pyaudio_instance = pyaudio.PyAudio()
        self._stream: pyaudio.Stream = None
        self._lock = threading.Lock()
        self._buffers: List[np.ndarray] = []
        self._active_input: Optional[int] = None
        self._current_input_name: Optional[str] = None
        self._subscribers: List[Callable] = []
        self._audio_devices = self._find_audio_devices()
    
    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def get_inputs(self) -> List[str]:
        return list(self._audio_devices.keys())
    
    def switch_input(self, input: str) -> None:
        if input not in self._audio_devices:
            raise ValueError(f"Input device '{input}' not found")
            
        if self.active:
            self._disconnect_input()
        
        self._active_input = self._audio_devices[input]
        self._current_input_name = input
        self.input_is_aux = False
        
        if self.active:
            self._connect_input()
        
        self._publish_input_switch()
    
    def activate(self) -> None:
        if not self._audio_devices:
            raise RuntimeError("No audio input devices available")
        if self._active_input is None:
            first_device_name = list(self._audio_devices.keys())[0]
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
            dev_info = self._pyaudio_instance.get_device_info_by_index(self._active_input)
            channels = min(dev_info['maxInputChannels'], 2)
            self.n_channels = channels 
            
            self._publish_input_switch()
            
            # Determine a valid sample rate for this device. 
            # Prefer device default, then the configured `_sample_rate`,
            # then common alternatives.
            device_default_rate = int(dev_info.get('defaultSampleRate', self._sample_rate))
            candidate_rates = [device_default_rate, int(self._sample_rate), 48000, 44100, 32000, 22050, 16000, 8000]
            seen = set()
            supported_rate = None
            for r in candidate_rates:
                if r in seen:
                    continue
                seen.add(r)
                try:
                    if self._pyaudio_instance.is_format_supported(
                        rate=r,
                        input_device=self._active_input,
                        input_channels=channels,
                        input_format=pyaudio.paFloat32,
                    ):
                        supported_rate = int(r)
                        break
                except Exception:
                    continue

            if supported_rate is None:
                # Fall back to device default or configured sample rate (may still fail)
                supported_rate = device_default_rate or int(self._sample_rate)

            self._stream = self._pyaudio_instance.open(
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
    

    def _disconnect_input(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None


    def _audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        if len(audio_data) == frame_count * 2:  # stereo
            left_channel = audio_data[::2]
            right_channel = audio_data[1::2]
            self._buffers = [left_channel.copy(), right_channel.copy()]
        else:  # mono
            self._buffers = [audio_data.copy()]
        self._process_callback(frame_count)
        return (None, pyaudio.paContinue)
    

    def _publish_input_switch(self) -> None:
        for callback in self._subscribers:
            callback()
    

    def get_buffers(self) -> List[np.ndarray]:
        buffers = self._buffers
        SCALAR_AUX_BOOST = .15
        if self.input_is_aux:
            buffers = [np.multiply(SCALAR_AUX_BOOST, b) for b in buffers]
        return buffers
    

    def _find_audio_devices(self) -> Dict[str, int]:
        audio_devices = {}
        self._add_loopback_devices(audio_devices)
        self._add_input_devices(audio_devices)
        return audio_devices
    

    def _add_loopback_devices(self, audio_devices: Dict[str, int]) -> None:
        wasapi_info = self._pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
        
        for i in range(self._pyaudio_instance.get_device_count()):
            dev = self._pyaudio_instance.get_device_info_by_index(i)
            
            if not self._is_device_usable(dev):
                continue
            
            if dev.get("isLoopbackDevice", False):
                audio_devices[f"{dev['name']} (Loopback)"] = i
            elif (dev['hostApi'] == wasapi_info['index'] and 
                    dev['maxInputChannels'] > 0 and
                    ('loopback' in dev['name'].lower() or
                    'stereo mix' in dev['name'].lower())):
                audio_devices[f"{dev['name']} (WASAPI Loopback)"] = i
    

    def _add_input_devices(self, audio_devices: Dict[str, int]) -> None:
        for i in range(self._pyaudio_instance.get_device_count()):
            dev = self._pyaudio_instance.get_device_info_by_index(i)
            
            if (self._is_device_usable(dev) and
                dev['maxInputChannels'] > 0 and 
                not dev.get("isLoopbackDevice", False) and
                not self._device_already_added(dev['name'], audio_devices)):
                
                host_api = self._pyaudio_instance.get_host_api_info_by_index(dev['hostApi'])
                device_name = dev['name']
                
                if host_api['name'] != 'MME':
                    device_name = f"{dev['name']} ({host_api['name']})"
                
                audio_devices[device_name] = i
                
    
    def _device_already_added(self, device_name: str, audio_devices: Dict[str, int]) -> bool:
        return (device_name in audio_devices or
                f"{device_name} (Loopback)" in audio_devices or
                f"{device_name} (WASAPI Loopback)" in audio_devices)
    
    def _is_device_usable(self, dev: dict) -> bool:
        """Check if device is enabled and usable (not disabled or hidden)."""
        # basic device validity
        if not dev.get('name') or not dev['name'].strip():
            return False
        # disabled devices often have 0.0
        if dev.get('defaultSampleRate', 0) <= 0:
            return False
        # suspicious names 
        name_lower = dev['name'].lower()
        disabled_indicators = [
            'microsoft sound mapper',
            'primary sound',
            'communications device',
            'disabled',
            'unavailable'
        ]
        if any(indicator in name_lower for indicator in disabled_indicators):
            return False
        return True
    
    def __del__(self):
        try:
            self.deactivate()
            if hasattr(self, '_pyaudio_instance') and self._pyaudio_instance:
                self._pyaudio_instance.terminate()
        except Exception:
            pass
