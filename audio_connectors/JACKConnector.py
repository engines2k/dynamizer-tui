import os
import jack
from dotenv import load_dotenv

from .AbstractConnector import AbstractConnector

load_dotenv()

class JACKConnector(AbstractConnector):
    def __init__(self, process_callback) -> None:
        self._client = jack.Client("Visualizer")
        self._client.inports.register("left")
        self._client.inports.register("right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self._shutdown_callback)
        self._input = os.getenv('DEFAULT_INPUT') or ""
        self.active = False


    @staticmethod
    def _shutdown_callback(status, reason):
        print("JACK shutdown:", status, reason)

    #TODO: Remove this method, clients should use an 'inputs' property instead
    @property
    def available_ports(self):
        return self._client.get_ports(is_midi=False)


    @property
    def inputs(self):
        return [ port for port in self._client.inports ]


    def activate(self):
        self._client.activate()
        self._connect_input()
        self.active = True


    def change_input(self, input):
        if self.active:
            self._disconnect_input()
        self._input = input
        if self.active:
            self._connect_input()


    def deactivate(self):
        self._client.deactivate()


    def _connect_input(self):
        if self._input:
            self._client.connect(f'{self._input}_FL', "Visualizer:left")
            self._client.connect(f'{self._input}_FR', "Visualizer:right")


    def _disconnect_input(self):
        for inport in self._client.inports:
            for connection in self._client.get_all_connections(inport):
                self._client.disconnect(connection, inport)

