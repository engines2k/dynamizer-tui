import os
import sounddevice as sd

from .abstractconnector import AbstractConnector

os.environ["SD_ENABLE_ASIO"] = "1"

class SDConnector(AbstractConnector):
    def __init__(self, process_callback) -> None:
        '''__init__'''
        self._active_input = None
        self._active_output = None
        self._active_stream = None
        # Get all devices and filter for input devices
        all_devices = sd.query_devices()
        self._inputs = [device for device in all_devices if device['max_input_channels'] > 0]
        self._client_callback = process_callback
        self._buffer = None


    @property
    def inputs(self):
        '''List all valid input devices as a dictionary of {pretty_name: device_index}.'''
        return {device['name']: device['index'] for device in self._inputs}
    
    def _stream_callback(self, indata, frames, time, status):
        if status:
            print(status)
        # Store audio input data for analysis (flatten to 1D for mono)
        self._buffer = indata.flatten()  # Convert 2D to 1D
        self._client_callback(frames)
    
    def activate(self) -> None:
        '''Activate the connnector to send signal.'''
        # Auto-select first available input device if none is selected
        if self._active_input is None and self._inputs:
            first_device = self._inputs[0]
            self._active_input = first_device['index']
        self._connect_input()


    def deactivate(self) -> None:
        '''Stop processing signal.'''
        self._disconnect_input()


    def get_buffer(self):        
        '''Get the current buffer of audio frames.'''
        if self._active_stream is not None:
            return self._buffer
        else:
            return None
 

    def change_input(self, input) -> None:
        '''Change the active input for the connector. (hot-swap ready)'''
        self._active_input = input
        if self._active_stream is not None:
            self._active_stream.stop()
            self._active_stream.close()
            self._connect_input()

    def _connect_input(self) -> None:
        '''Safely connect an input.'''
        if self._active_input is not None:
            # Use device index for connection
            device_idx = self._active_input if isinstance(self._active_input, int) else self._active_input
            if isinstance(device_idx, dict) and 'index' in device_idx:
                device_idx = device_idx['index']
            self._active_stream = sd.InputStream(device=device_idx, callback=self._stream_callback)
            self._active_stream.start()

    def _disconnect_input(self) -> None:
        '''Safely disconnect an input.'''
        if self._active_stream is not None:
            self._active_stream.stop()
            self._active_stream.close()
            self._active_stream = None
