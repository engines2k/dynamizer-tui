import pyaudiowpatch as pyaudio
import numpy as np
import threading
import time
from typing import Dict, List, Callable, Optional, Any
from .abstractconnector import AbstractConnector


class PAConnector(AbstractConnector):
    
    def __init__(self, process_callback: Callable):
        super().__init__()
        
        self.channel_config = "STEREO"
        self.active = False

        self._sample_rate = 44100
        self._buffer_size = 1024
        self._channels = 2
        self._process_callback = process_callback
        self._pyaudio_instance = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._lock = threading.Lock()
        self._buffers: List[np.ndarray] = []
        self._active_input: Optional[int] = None
        self._current_input_name: Optional[str] = None
        self._subscribers: List[Callable] = []
        self._loopback_devices = self._find_loopback_devices()
    
    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def get_inputs(self) -> List[str]:
        return list(self._loopback_devices.keys())
    
    def switch_input(self, input_name: str) -> None:
        if input_name not in self._loopback_devices:
            raise ValueError(f"Input device '{input_name}' not found")
            
        if self.active:
            self._disconnect_input()
        
        self._active_input = self._loopback_devices[input_name]
        self._current_input_name = input_name
        
        if self.active:
            self._connect_input()
        
        self._publish_input_switch()
    
    def activate(self) -> None:
        if not self._loopback_devices:
            raise RuntimeError("No WASAPI loopback devices available")
        
        if self._active_input is None:
            first_device_name = list(self._loopback_devices.keys())[0]
            self._active_input = self._loopback_devices[first_device_name]
            self._current_input_name = first_device_name
        
        self._connect_input()
        self.active = True
    
    def deactivate(self) -> None:
        self._disconnect_input()
        self.active = False
    
    def _connect_input(self) -> None:
        if self._active_input is None:
            raise RuntimeError("No loopback device selected")
        
        try:
            dev_info = self._pyaudio_instance.get_device_info_by_index(self._active_input)
            channels = min(dev_info['maxInputChannels'], 2)
            
            if channels == 1:
                self.channel_config = 'MONO'
            elif channels == 2:
                self.channel_config = 'STEREO'
            else:
                self.channel_config = f'{channels}CH'
            
            self._stream = self._pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=self._active_input,
                frames_per_buffer=self._buffer_size,
                stream_callback=self._audio_callback
            )
            
            self._stream.start_stream()
            
        except Exception as e:
            raise RuntimeError(f"Failed to connect to WASAPI loopback device: {e}")
    
    def _disconnect_input(self) -> None:
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            except Exception:
                pass
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        try:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            if len(audio_data) == frame_count * 2:  # Stereo
                left_channel = audio_data[::2]
                right_channel = audio_data[1::2]
                self._buffers = [left_channel.copy(), right_channel.copy()]
            else:  # Mono
                self._buffers = [audio_data.copy()]
            
            self._process_callback(frame_count)
            
        except Exception:
            pass
        
        return (None, pyaudio.paContinue)
    
    def _publish_input_switch(self) -> None:
        for callback in self._subscribers:
            callback()
    
    def get_buffers(self) -> List[np.ndarray]:
        return self._buffers
    
    def _find_loopback_devices(self) -> Dict[str, int]:
        loopback_devices = {}
        
        try:
            wasapi_info = self._pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
            
            for i in range(self._pyaudio_instance.get_device_count()):
                dev = self._pyaudio_instance.get_device_info_by_index(i)
                
                if dev.get("isLoopbackDevice", False):
                    loopback_devices[dev['name']] = i
                elif (dev['hostApi'] == wasapi_info['index'] and 
                      dev['maxInputChannels'] > 0 and
                      ('loopback' in dev['name'].lower() or
                       'stereo mix' in dev['name'].lower())):
                    loopback_devices[f"{dev['name']} (WASAPI)"] = i
                    
        except (OSError, Exception):
            pass
        
        return loopback_devices
    
    def __del__(self):
        try:
            self.deactivate()
            if hasattr(self, '_pyaudio_instance') and self._pyaudio_instance:
                self._pyaudio_instance.terminate()
        except Exception:
            pass