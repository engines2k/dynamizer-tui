import pyaudiowpatch as pyaudio
import numpy as np
import threading
import time
from typing import Dict

from .abstractconnector import AbstractConnector

class PAConnector(AbstractConnector):
    def __init__(self, process_callback) -> None:
        '''Initialize PyAudioWPatch connector with WASAPI loopback support'''
        self._process_callback = process_callback
        self._active_input = None
        self._pa_stream = None
        self._pyaudio_instance = None
        self._buffer = None
        self._sample_rate = 44100
        self._buffer_size = 1024
        self.active = False
        
        # Get available loopback devices
        self._loopback_devices = self._find_loopback_devices()

    @property
    def inputs(self) -> Dict[str, str]:
        '''List all valid WASAPI loopback devices as a dictionary of {pretty_name: device_index}.'''
        return self._loopback_devices

    def activate(self) -> None:
        '''Activate the connector to start WASAPI loopback recording.'''
        if not self._loopback_devices:
            print("No WASAPI loopback devices available!")
            print("PyAudioWPatch couldn't find any loopback endpoints.")
            return
            
        # Auto-select first available loopback device if none selected
        if self._active_input is None:
            first_device_name = list(self._loopback_devices.keys())[0]
            self._active_input = self._loopback_devices[first_device_name]
            print(f"Auto-selected loopback device: {first_device_name}")
            
        self._connect_input()
        self.active = True

    def deactivate(self) -> None:
        '''Stop processing signal.'''
        self._disconnect_input()
        self.active = False

    def get_buffer(self):
        '''Get the current buffer of audio frames.'''
        return self._buffer

    def change_input(self, input_device) -> None:
        '''Change the active input device for loopback recording.'''
        was_active = self.active
        if was_active:
            self.deactivate()
        self._active_input = input_device
        if was_active:
            self.activate()

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

    def _connect_input(self) -> None:
        '''Safely connect to WASAPI loopback device.'''
        if self._active_input is None:
            print("No loopback device selected")
            return
            
        try:
            print(f"Connecting to WASAPI loopback device index: {self._active_input}")
            
            self._pyaudio_instance = pyaudio.PyAudio()
            
            # Get device info to determine channels
            dev_info = self._pyaudio_instance.get_device_info_by_index(self._active_input)
            channels = min(dev_info['maxInputChannels'], 2)  # Use stereo or mono
            
            print(f"Device: {dev_info['name']}")
            print(f"Channels: {channels}")
            print(f"Sample Rate: {self._sample_rate}")
            
            self._pa_stream = self._pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=self._active_input,
                frames_per_buffer=self._buffer_size,
                stream_callback=self._audio_callback
            )
            
            self._pa_stream.start_stream()
            print("WASAPI loopback recording started successfully!")
            print("Play some system audio to see analysis results...")
            
        except Exception as e:
            print(f"Error connecting to loopback device: {e}")
            print("\\nTroubleshooting:")
            print("1. Try running as administrator")
            print("2. Check Windows Sound settings for enabled recording devices")
            print("3. Verify the device supports loopback recording")

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
                
            # Convert bytes to numpy array and flatten to 1D
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Handle stereo to mono conversion if needed
            if len(audio_data) == frame_count * 2:  # Stereo
                audio_data = audio_data[::2]  # Take left channel only
            
            self._buffer = audio_data.copy()
            self._process_callback(frame_count)
            
        except Exception as e:
            print(f"Audio callback error: {e}")
            
        return (None, pyaudio.paContinue)

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