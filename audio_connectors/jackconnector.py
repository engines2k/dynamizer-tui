import os
import re
import jack
from dotenv import load_dotenv
from typing import Dict, List, Tuple


from .abstractconnector import AbstractConnector

load_dotenv()

class JACKConnector(AbstractConnector):
    def __init__(self, process_callback) -> None:
        self._client = jack.Client("dynamizer")
        self._client.inports.register("left")
        self._client.inports.register("right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self._shutdown_callback)
        self._input = os.getenv('DEFAULT_INPUT') or ""
        self._inputs: Dict[str, str] = {}
        self.active = False


    def activate(self):
        self._client.activate()
        self._connect_input()
        self.active = True


    def get_inputs(self) -> Dict[str, str]:
        self._inputs = { 
            self._pretty_input_label(port.name): port.name
            for port in self._client.get_ports(is_midi=False)
            if self._valid_outport(port)
        }
        return self._inputs


    def change_input(self, input):
        if self.active:
            self._disconnect_input()
        self._input = input
        if self.active:
            self._connect_input()


    def get_buffer(self):        
        frame = self._client.inports[0].get_array()  # type: ignore[attr-defined]
        return frame


    def deactivate(self):
        self._client.deactivate()
        self.active = False


    def _connect_input(self):
        if self._input:
            try:
                _, _, channel = self._split_port_name(self._input)
                self._client.connect(f'{self._input}', f'dynamizer:left')
            except jack.JackErrorCode as e:
                if "already exists" not in str(e):
                    raise SystemError(f"Could not connect to input '{self._input}': {e}")


    def _split_port_name(self, name: str) -> Tuple:
        '''Return a tuple of the port label, type, and channel'''
        pattern = r'(\w+):(\w+)_(\w+)'
        match = re.search(pattern, name)
        return (match.group(1), match.group(2), match.group(3)) if match else (None, None, None)


    def _disconnect_input(self):
        for inport in self._client.inports:
            for connection in self._client.get_all_connections(inport):
                self._client.disconnect(connection, inport)


    def _valid_outport(self, port: jack.Port):
        _, port_type, _ = self._split_port_name(port.name)
        if port_type in {'capture', 'monitor', 'output'}:
            return True
        return False


    @staticmethod
    def _pretty_input_label(label: str) -> str:
        return label
        pretty = re.sub(r':(monitor|output)_\w\w', "", label)
        return pretty


    @staticmethod
    def _shutdown_callback(status, reason):
        print("JACK shutdown:", status, reason)

