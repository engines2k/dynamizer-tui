import os
import re
import jack
from dotenv import load_dotenv
from typing import Callable, DefaultDict, List
from collections import defaultdict


from .abstractconnector import AbstractConnector

load_dotenv()

class JACKConnector(AbstractConnector):

    def __init__(self, process_callback) -> None:
        self._client = jack.Client("dynamizer")
        self._client.inports.register("input_left")
        self._client.inports.register("input_right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self._shutdown_callback)
        self._input = os.getenv('DEFAULT_INPUT') or ""
        self._available_outports: DefaultDict[str, list] = defaultdict(list)
        self.channel_config: str
        self._subscribers: List[Callable] = []
        self.active = False


    def activate(self):
        self._client.activate()
        self.get_inputs()
        self._connect_input()
        self.active = True


    def get_inputs(self) -> List[str]:
        self._available_outports.clear()
        for port in self._client.get_ports(is_midi=False):
            if self._valid_outport(port):
                port_details = self._parse_port_name(port.name)
                self._available_outports[port_details['device']].append(port.name)
                
        return list(self._available_outports.keys())


    def switch_input(self, input: str):
        if self.active:
            self._disconnect_input()
        self._input = input
        if self.active:
            self._connect_input()


    def get_buffers(self):        
        frame = self._client.inports[0].get_array()  # type: ignore[attr-defined]
        return frame


    def deactivate(self):
        self._client.deactivate()
        self.active = False


    def _connect_input(self):
        if self._input:
            input_outports = self._available_outports[self._input]
            try:
                if len(input_outports) == 1:
                    self._client.connect(f'{input_outports[0]}', f'dynamizer:input_left')
                    self.channel_config = 'MONO'
                elif len(input_outports) == 2:
                    self._client.connect(f'{input_outports[0]}', f'dynamizer:input_left')
                    self._client.connect(f'{input_outports[1]}', f'dynamizer:input_right')
                    self.channel_config = 'STEREO'
                self._publish_input_switch()

            except jack.JackErrorCode as e:
                if "already exists" not in str(e):
                    raise SystemError(f"Could not connect to outports '{self._input}': {e}")


    def _publish_input_switch(self):
        for callable in self._subscribers:
            callable()


    def _parse_port_name(self, name: str) -> dict:
        '''Return a dict of the port device, type, and channel'''
        pattern = r'(?P<device>.*):(?P<type>[^_]+)(?:_(?P<channel>.*))?'
        match = re.search(pattern, name)
        if not match:
            raise Exception(f'Unable to parse port name "{name}"')
        return match.groupdict()

    def _disconnect_input(self):
        for inport in self._client.inports:
            for connection in self._client.get_all_connections(inport):
                self._client.disconnect(connection, inport)


    def _valid_outport(self, port: jack.Port):
        valid_port_types = {'capture', 'monitor', 'output'}
        port_details = self._parse_port_name(port.name)
        if isinstance(port, jack.OwnPort) or port_details['type'] not in valid_port_types:
            return False
        return True


    @staticmethod
    def _shutdown_callback(status, reason):
        print("JACK shutdown:", status, reason)

