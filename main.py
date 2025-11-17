import jack
import numpy as np
import time
from scipy.signal import ZoomFFT
from collections import deque

# lol
LEFT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FL"
RIGHT_MONITOR = "Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FR"
#LEFT_MONITOR = "Built-in Audio Analog Stereo:monitor_FL"
#RIGHT_MONITOR = "Built-in Audio Analog Stereo:monitor_FR"

def a_weighting(f):
    numerator = 12194**2 * f**4
    denominator = ((f**2 + 20.6**2) * np.sqrt((f**2 + 107.7**2) * (f**2 + 737.9**2)) * (f**2 + 12194**2))
    weight_linear = numerator / denominator
    weight_db = 20 * np.log10(weight_linear) - 20 * np.log10(a_weighting_1khz())
    return weight_db

def a_weighting_1khz():
    f = 1000
    return 12194**2 * f**4 / ((f**2 + 20.6**2) * np.sqrt((f**2 + 107.7**2) * (f**2 + 737.9**2)) * (f**2 + 12194**2))

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
    hop_size = 256

    def __init__(self):
        self.failures = 0
        self.inbuffer = np.ndarray(1)
        self.last_2_frames = deque(maxlen=2)
        self.pause_processing = False
        self.audio_connector = AudioConnector(self.process_callback)

        self.hanning_window = np.hanning(self.frame_size)
        self.low_fft = ZoomFFT(self.frame_size, [20, 100], 80, fs=self.sample_rate)
        self.mid_fft = ZoomFFT(self.frame_size, [100, 1000], 100, fs=self.sample_rate)
        self.high_fft = ZoomFFT(self.frame_size, [1000, 20000], 100, fs=self.sample_rate)

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

        while len(self.inbuffer) >= self.frame_size + self.hop_size:
            frame = self.inbuffer[:self.frame_size]
            self.inbuffer = self.inbuffer[self.hop_size:]
            bins = self.analyze_freqs(frame)
            print(self.primitive_analyzer(bins))

    def analyze_freqs(self, x):
        x = x * self.hanning_window
        low_freqs = self.low_fft(x)
        mid_freqs = self.mid_fft(x)
        high_freqs = self.high_fft(x)
        combined = np.concatenate((low_freqs, mid_freqs, high_freqs))
        magnitudes = np.abs(combined)
        dbs = 20 * np.log10(magnitudes + 1e-10)  # Avoid log(0)
        return dbs + self.apply_a_weighting()

    def apply_a_weighting(self):
        bin_freqs = self.get_bin_freqs()
        return np.array([a_weighting(freq) for freq in bin_freqs])

    def get_bin_freqs(self):
        return np.concatenate((np.linspace(20, 80, 80), np.linspace(100, 1000, 100), np.linspace(1000, 20000, 100)))

    @staticmethod
    def primitive_analyzer(freqs):
        res = ""
        for i in range(0, len(freqs), 2):
            strength = freqs[i]
            if strength > 2:
                res += f"{strength % 100:1.0f} "
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
        print("Dynamizer starting. Press Ctrl+C to quit.")
        time.sleep(1)
        dynamizer.activate()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

        print("Dynamizer shutting down, goodbye")
