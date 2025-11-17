import jack
import numpy as np
import time
from itertools import chain
from scipy.signal import zoom_fft
from collections import deque

# lol
LEFT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FL"
RIGHT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FR"
#LEFT_MONITOR = "Built-in Audio Analog Stereo:monitor_FL"
#RIGHT_MONITOR = "Built-in Audio Analog Stereo:monitor_FR"

class AudioConnector():
    def __init__(self, process_callback) -> None:
        self._client = jack.Client("Visualizer")
        self._client.inports.register("left")
        self._client.inports.register("right")
        self._client.set_process_callback(process_callback)
        self._client.set_shutdown_callback(self.shutdown)

    def shutdown(self, status, reason):
        print("JACK shutdown:", status, reason)

    def activate(self):
        self._client.activate()
        self.connect_devices()

    def deactivate(self):
        self._client.deactivate()

    def connect_devices(self):
        self._client.connect(LEFT_MONITOR, "Visualizer:left")
        self._client.connect(RIGHT_MONITOR, "Visualizer:right")

    @property
    def inports(self):
        return self._client.inports

#TODO: Use bisect(?) to implement a method that returns the bin for a given frequency.
class Dynamizer():
    max_failures = 3
    sample_rate = 44100
    sample_d = 1 / sample_rate
    frame_size = 4096
    hop_size = 512

    def __init__(self):
        self.failures = 0
        self.inbuffer = np.ndarray(1)
        self.last_2_frames = deque(maxlen=2)
        self.pause_processing = False
        self.audio_connector = AudioConnector(self.process_callback)

    def activate(self):
        self.audio_connector.activate()

    def process_callback(self, n_frames):
        if not self.pause_processing:
            self.process_frame(n_frames)

    def process_frame(self, n_frames):
        if len(self.inbuffer) > self.sample_rate // 2:
            self.recover()
        inports = self.audio_connector.inports
        frame = inports[0].get_array() # type: ignore
        self.inbuffer = np.concatenate((self.inbuffer, frame))
        if(len(self.inbuffer) >= self.frame_size + self.hop_size):
            frame = self.inbuffer[:self.frame_size]
            self.inbuffer = self.inbuffer[self.hop_size:]
            bins = self.analyze_freqs(frame)
            print(self.primitive_analyzer(bins))

    def analyze_freqs(self, x):
        windowed = x * np.hanning(len(x))
        low_freqs = zoom_fft(windowed, [20, 100], 80, fs=self.sample_rate)
        mid_freqs = zoom_fft(windowed, [100, 1000], 100, fs=self.sample_rate)
        high_freqs = zoom_fft(windowed, [1000, 20000], 100, fs=self.sample_rate)
        return np.concatenate((low_freqs, np.multiply(mid_freqs, 3), np.multiply(high_freqs, 80)))

    @staticmethod
    def primitive_analyzer(freqs):
        res = ""
        for i in range(0, len(freqs), 2):
            mag = np.abs(freqs[i])
            if i < 5:
                res += " "
            if mag > 50:
                res += f"{mag//10:1.0f} "
            else:
                res += " ."
        return res

    @staticmethod
    def shutdown(status, reason):
        print("JACK shutdown:", status, reason)

    def look_for_transients(self):
        pass

    def recover(self):
        if self.failures >= self.max_failures:
            print("3 buffer processing fallbehinds. Using easier hop size.")
            self.hop_size = 1024
            self.failures = 0
        else:
            print("Half a second behind! Attempting recovery by clearing buffer.")
            self.failures += 1
        self.toggle_pause()
        self.inbuffer = np.ndarray(1)
        time.sleep(.5)
        self.toggle_pause()


    def toggle_pause(self):
        self.pause_processing = not self.pause_processing
        status = "PAUSED" if self.pause_processing else "RESUMED"
        print(f"\nProcessing {status}")

dynamizer = Dynamizer()

if __name__ == "__main__":

        #print(np.fft.fftfreq(512, d=(1/44100)))
        print("Dynamizer starting. Press Ctrl+C to quit.")
        time.sleep(1)
        dynamizer.activate()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

        print("Dynamizer shutting down, goodbye")
