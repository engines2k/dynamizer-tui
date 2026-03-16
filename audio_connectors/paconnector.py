import pyaudiowpatch as pyaudio
import numpy as np
import threading
import time
from typing import Dict, List, Callable, Optional, Any
from .abstractconnector import AbstractConnector


class PAConnector(AbstractConnector):
    """PulseAudio/PortAudio connector for audio input using PyAudioWPatch with WASAPI loopback support."""
    
    def __init__(self, process_callback: Callable):
        super().__init__()
        
        # Core audio parameters
        self.sample_rate = 44100
        self.buffer_size = 1024
        self.channels = 2
        self.channel_config = "STEREO"
        
        # Process callback from master analyzer
        self._process_callback = process_callback
        
        # PyAudio instance
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
        # Threading and state
        self.active = False
        self._lock = threading.Lock()
        
        # Buffer management
        self._buffers: List[np.ndarray] = []
        
        # Current input device
        self._active_input: Optional[int] = None
        self._current_input_name: Optional[str] = None
        
        # Subscriber system for notifications
        self._subscribers: List[Callable] = []
        
        # Device management
        self._loopback_devices = self._find_loopback_devices()
    
    def subscribe(self, callback: Callable) -> None:
        """Subscribe to input switch events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def get_inputs(self) -> List[str]:
        """Get list of available audio input devices."""
        return list(self._loopback_devices.keys())
    
    def switch_input(self, input_name: str) -> None:
        """Switch to a different audio input device."""
        if self.active:
            self._disconnect_input()
        
        # Find device index for the input name
        if input_name in self._loopback_devices:
            self._active_input = self._loopback_devices[input_name]
            self._current_input_name = input_name
        
        if self.active:
            self._connect_input()
        
        self._publish_input_switch()
    
    def activate(self) -> None:
        """Activate the connector to start WASAPI loopback recording."""
        if not self._loopback_devices:
            print("No WASAPI loopback devices available!")
            print("PyAudioWPatch couldn't find any loopback endpoints.")
            return
        
        # Auto-select first available loopback device if none selected
        if self._active_input is None:
            first_device_name = list(self._loopback_devices.keys())[0]
            self._active_input = self._loopback_devices[first_device_name]
            self._current_input_name = first_device_name
            print(f"Auto-selected loopback device: {first_device_name}")
        
        self._connect_input()
        self.active = True
    
    def deactivate(self) -> None:
        """Stop processing signal."""
        self._disconnect_input()
        self.active = False
    
    def _connect_input(self) -> None:
        """Safely connect to WASAPI loopback device."""
        if self._active_input is None:
            print("No loopback device selected")
            return
        
        try:
            print(f"Connecting to WASAPI loopback device index: {self._active_input}")
            
            # Get device info to determine channels
            dev_info = self.pyaudio_instance.get_device_info_by_index(self._active_input)
            channels = min(dev_info['maxInputChannels'], 2)  # Use stereo or mono
            
            # Set channel configuration
            if channels == 1:
                self.channel_config = 'MONO'
            elif channels == 2:
                self.channel_config = 'STEREO'
            else:
                self.channel_config = f'{channels}CH'
            
            print(f"Device: {dev_info['name']}")
            print(f"Channels: {channels} ({self.channel_config})")
            print(f"Sample Rate: {self.sample_rate}")
            
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self._active_input,
                frames_per_buffer=self.buffer_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            print("WASAPI loopback recording started successfully!")
            print("Play some system audio to see analysis results...")
            
        except Exception as e:
            print(f"Error connecting to loopback device: {e}")
            print("\nTroubleshooting:")
            print("1. Try running as administrator")
            print("2. Check Windows Sound settings for enabled recording devices")
            print("3. Verify the device supports loopback recording")
    
    def _disconnect_input(self) -> None:
        """Safely disconnect from WASAPI loopback device."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                print("WASAPI loopback recording stopped")
            except Exception as e:
                print(f"Error stopping stream: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudioWPatch WASAPI loopback."""
        try:
            if status:
                print(f"Audio status: {status}")
            
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Handle mono vs stereo data
            if len(audio_data) == frame_count * 2:  # Stereo
                # Split into left and right channels
                left_channel = audio_data[::2]
                right_channel = audio_data[1::2]
                self._buffers = [left_channel.copy(), right_channel.copy()]
            else:  # Mono
                self._buffers = [audio_data.copy()]
            
            # Call the process callback
            self._process_callback(frame_count)
            
        except Exception as e:
            print(f"Audio callback error: {e}")
        
        return (None, pyaudio.paContinue)
    
    def _publish_input_switch(self) -> None:
        """Notify all subscribers that the input has switched."""
        for callback in self._subscribers:
            callback()
    
    def get_buffers(self) -> List[np.ndarray]:
        """Get the channel buffers of audio frames."""
        return self._buffers
    
    def _find_loopback_devices(self) -> Dict[str, int]:
        """Find available WASAPI loopback devices using PyAudioWPatch."""
        loopback_devices = {}
        
        try:
            print("Searching for WASAPI loopback devices with PyAudioWPatch...")
            
            print("\n=== ALL DEVICES ===")
            for i in range(self.pyaudio_instance.get_device_count()):
                dev = self.pyaudio_instance.get_device_info_by_index(i)
                print(f"[{i}] {dev['name']} | in:{dev['maxInputChannels']} out:{dev['maxOutputChannels']} | hostApi:{dev['hostApi']}")
            
            print("\n=== WASAPI LOOPBACK DEVICES ===")
            try:
                wasapi_info = self.pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
                print(f"WASAPI Host API found: {wasapi_info['name']}")
                
                for i in range(self.pyaudio_instance.get_device_count()):
                    dev = self.pyaudio_instance.get_device_info_by_index(i)
                    
                    # Check if this is a loopback device
                    if dev.get("isLoopbackDevice", False):
                        device_name = dev['name']
                        loopback_devices[device_name] = i
                        print(f"[{i}] Found WASAPI loopback: {device_name}")
                    
                    # Also check for WASAPI devices that might be loopback-capable 
                    elif (dev['hostApi'] == wasapi_info['index'] and 
                          dev['maxInputChannels'] > 0 and
                          ('loopback' in dev['name'].lower() or
                           'stereo mix' in dev['name'].lower() or
                           'what u hear' in dev['name'].lower())):
                        device_name = f"{dev['name']} (WASAPI)"
                        loopback_devices[device_name] = i
                        print(f"[{i}] Found potential WASAPI loopback: {device_name}")
                
            except OSError:
                print("WASAPI Host API not found!")
            
            if not loopback_devices:
                print("No loopback devices found!")
                print("Enable 'Stereo Mix' in Windows Sound settings or use VB-Cable virtual audio cable.")
            
        except Exception as e:
            print(f"Error finding loopback devices: {e}")
        
        return loopback_devices
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.deactivate()
            if hasattr(self, 'pyaudio_instance') and self.pyaudio_instance:
                self.pyaudio_instance.terminate()
        except Exception:
            pass  # Ignore cleanup errors

    def _disconnect_input(self) -> None:
        '''Safely disconnect from WASAPI loopback device.'''
        if self._pa_stream:
            try:
                self._pa_stream.stop_stream()
                self._pa_stream.close()
                self._pa_stream = None
                print("WASAPI loopback recording stopped")
            except Exception as e:
                print(f"Error stopping stream: {e}")
                
        if self._pyaudio_instance:
            try:
                self._pyaudio_instance.terminate()
                self._pyaudio_instance = None
            except Exception as e:
                print(f"Error terminating PyAudio: {e}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        '''Callback for PyAudioWPatch WASAPI loopback'''
        try:
            if status:
                print(f"Audio status: {status}")
                
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Handle mono vs stereo data
            if len(audio_data) == frame_count * 2:  # Stereo
                # Split into left and right channels
                left_channel = audio_data[::2]
                right_channel = audio_data[1::2]
                self._buffers = [left_channel.copy(), right_channel.copy()]
            else:  # Mono
                self._buffers = [audio_data.copy()]
            
            self._process_callback(frame_count)
            
        except Exception as e:
            print(f"Audio callback error: {e}")
            
        return (None, pyaudio.paContinue)

    def _publish_input_switch(self):
        '''Notify all subscribers that the input has switched.'''
        for callable in self._subscribers:
            callable()

    def _find_loopback_devices(self) -> Dict[str, str]:
        '''Find available WASAPI loopback devices using PyAudioWPatch.'''
        loopback_devices = {}
        
        try:
            print("Searching for WASAPI loopback devices with PyAudioWPatch...")
            
            with pyaudio.PyAudio() as p:
                print("\\n=== ALL DEVICES ===")
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    print(f"[{i}] {dev['name']} | in:{dev['maxInputChannels']} out:{dev['maxOutputChannels']} | hostApi:{dev['hostApi']}")
                
                print("\\n=== WASAPI LOOPBACK DEVICES ===")
                try:
                    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                    print(f"WASAPI Host API found: {wasapi_info['name']}")
                    
                    for i in range(p.get_device_count()):
                        dev = p.get_device_info_by_index(i)
                        
                        # Check if this is a loopback device
                        if dev.get("isLoopbackDevice", False):
                            device_name = dev['name']
                            loopback_devices[device_name] = i
                            print(f"[{i}] Found WASAPI loopback: {device_name}")
                        
                        # Also check for WASAPI devices that might be loopback-capable 
                        elif (dev['hostApi'] == wasapi_info['index'] and 
                              dev['maxInputChannels'] > 0 and
                              ('loopback' in dev['name'].lower() or
                               'stereo mix' in dev['name'].lower() or
                               'what u hear' in dev['name'].lower())):
                            device_name = f"{dev['name']} (WASAPI)"
                            loopback_devices[device_name] = i
                            print(f"[{i}] Found WASAPI device (potential loopback): {device_name}")
                            
                except OSError as e:
                    print(f"WASAPI not available: {e}")
                    
        except Exception as e:
            print(f"Error finding loopback devices: {e}")
            
        if not loopback_devices:
            print("\\nNo WASAPI loopback devices found.")
            print("\\nThis could mean:")
            print("1. Your audio drivers don't expose WASAPI loopback endpoints")
            print("2. You may need to enable 'Stereo Mix' in Windows Sound settings")
            print("3. Professional audio interfaces (like Focusrite) often don't expose loopback")
            print("4. Try enabling process-specific loopback on Windows 10 20H1+")
            
        return loopback_devices

    def list_all_devices(self) -> None:
        '''Debug method to list all available audio devices.'''
        try:
            with pyaudio.PyAudio() as p:
                print("\\n=== ALL PYAUDIOWPATCH DEVICES ===")
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    host_api = p.get_host_api_info_by_index(dev['hostApi'])
                    loopback_flag = dev.get("isLoopbackDevice", False)
                    print(f"[{i}] {dev['name']}")
                    print(f"    Host API: {host_api['name']}")
                    print(f"    Input channels: {dev['maxInputChannels']}")
                    print(f"    Output channels: {dev['maxOutputChannels']}")
                    print(f"    Is Loopback: {loopback_flag}")
                    print(f"    Default sample rate: {dev['defaultSampleRate']}")
                    print()
        except Exception as e:
            print(f"Error listing devices: {e}")

    def try_process_loopback(self, process_name: str = None) -> bool:
        '''Try Windows 10 20H1+ process-specific loopback (experimental)'''
        print("\\nAttempting process-specific WASAPI loopback...")
        print("This feature requires Windows 10 20H1+ and is experimental")
        
        # This would need additional implementation for process-specific capture
        # For now, just indicate the feature exists
        print("Process-specific loopback not yet implemented in this connector")
        print("Contact developer for process loopback implementation")
        return False