import os
import jack
from dotenv import load_dotenv

__all__ = ["AudioConnector"]

load_dotenv()

INPUT_LEFT = os.getenv('INPUT_LEFT') or ""
INPUT_RIGHT = os.getenv('INPUT_RIGHT') or ""

class AudioConnector():
    def __init__(self, process_callback) -> None:
        self._client = jack.Client("Visualizer")
        self._client.inports.register("left")
        self._client.inports.register("right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self.shutdown_callback)

    @staticmethod
    def shutdown_callback(status, reason):
        print("JACK shutdown:", status, reason)

    def activate(self):
        self._client.activate()
        self._connect_devices()

    def deactivate(self):
        self._client.deactivate()

    def _connect_devices(self):
        self._client.connect(INPUT_LEFT, "Visualizer:left")
        self._client.connect(INPUT_RIGHT, "Visualizer:right")

    @property
    def inports(self):
        return self._client.inports

