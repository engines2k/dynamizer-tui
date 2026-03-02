import os
import jack
from dotenv import load_dotenv

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

    def _connect_input(self):
        if self._input:
            self._client.connect(f'{self._input}_FL', "Visualizer:left")
            self._client.connect(f'{self._input}_FR', "Visualizer:right")


    def set_input(self, input):
        self._input = input

    def change_input(self, input):
        if self._active:
            self._disconnect_input()
        self._input = input
        if self._active:
            self._connect_input()

    def _disconnect_input(self):
        if self._input:
            self._client.disconnect(f'{self._input}_FL', "Visualizer:left")
            self._client.disconnect(f'{self._input}_FR', "Visualizer:right")


    def deactivate(self):
        self._client.deactivate()


    @property
    def inports(self):
        return self._client.inports

