import jack
import numpy as np
import time
import sys
import threading
import tty
import termios
from itertools import chain

# lol
LEFT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FL"
RIGHT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FR"

class AudioConnector():
    def __init__(self, process_callback) -> None:
        self.client = jack.Client("Visualizer")
        self.client.inports.register("left")
        self.client.inports.register("right")
        self.client.set_process_callback(process_callback)
        self.client.set_shutdown_callback(self.shutdown)

    def shutdown(self, status, reason):
        print("JACK shutdown:", status, reason)

    def activate(self):
        self.client.activate()

    def deactivate(self):
        self.client.deactivate()

    def connect_devices(self):
        self.client.connect(LEFT_MONITOR, "Visualizer:left")
        self.client.connect(RIGHT_MONITOR, "Visualizer:right")

    @property
    def inports(self):
        return self.client.inports

class Dynamizer():
    sample_rate = 44100
    sample_d = 1 / sample_rate

    def __init__(self):
        self.pause_processing = False
        self.audio_connector = AudioConnector(self.process_callback)

    def activate(self):
        self.audio_connector.activate()
        self.audio_connector.connect_devices()

    def process_callback(self, n_frames):
        if not self.pause_processing:
            self.process_frame(n_frames)

    def process_frame(self, n_frames):
        inports = self.audio_connector.inports
        # Get frequency bins
        frame = inports[0].get_array() # type: ignore
        fourier = np.fft.fft(frame)

        res = ""
        for i in chain(range(1, 6, 2),  range(7, len(fourier.real-50), 13)):
            mag = np.abs(fourier.real[i])  # bin near ~88 Hz
            if i < 5:
                res += " "
            if mag > 3/i*18:
                res += f" {mag:1.0f} "
            else:
                res += " . "
        print(res)

    def shutdown(self, status, reason):
        print("JACK shutdown:", status, reason)

    def toggle_pause(self):
        self.pause_processing = not self.pause_processing
        status = "PAUSED" if self.pause_processing else "RESUMED"
        print(f"\nProcessing {status}")

dynamizer = Dynamizer()

if __name__ == "__main__":
        print("Dynamizer starting. Press Ctrl+C to quit.")
        time.sleep(1)
        dynamizer.activate()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

        print("Dynamizer shutting down, goodbye")
