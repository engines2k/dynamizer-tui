import os
import re
import jack
from dotenv import load_dotenv
from typing import Dict

__all__ = ["AudioConnector"]

load_dotenv()

class AudioConnector():
    def __init__(self, process_callback) -> None:
        self._client = jack.Client("Visualizer")
        self._client.inports.register("left")
        self._client.inports.register("right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self.shutdown_callback)
        self._active = False
        self._input = os.getenv('DEFAULT_INPUT') or ""

    @staticmethod
    def shutdown_callback(status, reason):
        print("JACK shutdown:", status, reason)


    @property
    def available_ports(self):
        return self._client.get_ports(is_midi=False)


    def activate(self):
        self._client.activate()
        self._connect_input()
        self._active = True

    def get_available_ports(self) -> Dict[str, str]:
        result = {}
        ports = self.available_ports
        valid_ports = [ port for port in ports if self.valid_outport(port) ]
        for port in valid_ports:
            result[self._pretty_port_name(port.name)] = port.name[:-3]
        return result
        

    @staticmethod
    def _pretty_port_name(pretty: str) -> str:
        pretty = re.sub(r':(monitor|output)_\w\w', "", pretty)
        return pretty

    @staticmethod
    def valid_outport(port: jack.Port):
        if ('capture' in port.name or 'playback' in port.name) or ('FL' not in port.name):
            return False
        return True

    def _connect_input(self):
        if self._input:
            try:
                self._client.connect(f'{self._input}_FR', "Visualizer:right")
                self._client.connect(f'{self._input}_FL', "Visualizer:left")
            except jack.JackErrorCode as e:
                if "already exists" not in str(e):
                    print(f"Warning: Could not connect to input '{self._input}': {e}")


    def set_input(self, input):
        self._input = input

    def change_input(self, input):
        if self._active:
            self._disconnect_input()
        self._input = input
        if self._active:
            self._connect_input()

    def _disconnect_input(self):
        for inport in self._client.inports:
            for connection in self._client.get_all_connections(inport):
                self._client.disconnect(connection, inport)


    def deactivate(self):
        self._client.deactivate()


    @property
    def inports(self):
        return self._client.inports

