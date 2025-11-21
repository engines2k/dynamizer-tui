import time
from weightings import a_weighting
from visualizers import analyzer, bass_beat
from audio_connector import AudioConnector
from collections import deque
import numpy as np
from scipy.signal import ZoomFFT

__all__ = ["dynamizer"]

class Dynamizer():
    max_failures = 3
    sample_rate = 44100
    sample_d = 1 / sample_rate
    window_size = 4096
    hop_size = 64

    def __init__(self):
        self.failures = 0
        self.inbuffer = np.ndarray(1)
        self.pause_processing = False
        self.audio_connector = AudioConnector(self.process_callback)

        self.hanning_window = np.hanning(self.window_size)
        self.low_zoom_fft = ZoomFFT(self.window_size, [20, 100], 80, fs=self.sample_rate)
        self.mid_zoom_fft = ZoomFFT(self.window_size, [100, 1000], 100, fs=self.sample_rate)
        self.high_zoom_fft = ZoomFFT(self.window_size, [1000, 20000], 100, fs=self.sample_rate)
        self.weightings = self.calc_a_weighting()

    def calc_a_weighting(self):
        bin_freqs = self._get_bin_freqs()
        return np.array([a_weighting(freq) for freq in bin_freqs])

    def activate(self) -> None:
        self.audio_connector.activate()

    def process_callback(self, n_frames: int) -> None:
        if not self.pause_processing:
            self.process_frames(n_frames)

    def process_frames(self, n_frames: int) -> None:
        if len(self.inbuffer) > self.sample_rate // 4:
            self.attempt_recovery()

        self._load_frames_into_buffer()

        while self._buffer_ready():
            self._process_buffer_window()

    def _load_frames_into_buffer(self) -> None:
        inports = self.audio_connector.inports
        frame = inports[0].get_array() # type: ignore
        self.inbuffer = np.concatenate((self.inbuffer, frame))

    def _buffer_ready(self):
        return len(self.inbuffer) >= self.window_size + self.hop_size

    def _process_buffer_window(self):
        window = self.inbuffer[:self.window_size]
        self.inbuffer = self.inbuffer[self.hop_size:]
        bins = self._analyze_window(window)
        self._output_result(bins)

    def _analyze_window(self, x):
        x = self._apply_window_function(x)
        freqs = self._apply_fft_strategy(x)
        freqs = self._transform_freqs(freqs)
        return freqs

    def _apply_window_function(self, x):
        return x * self.hanning_window

    def _apply_fft_strategy(self, x):
        low_freqs = self.low_zoom_fft(x)
        mid_freqs = self.mid_zoom_fft(x)
        high_freqs = self.high_zoom_fft(x)
        return np.concatenate((low_freqs, mid_freqs, high_freqs))

    def _transform_freqs(self, freqs):
        freqs = np.abs(freqs**2)
        freqs = 20 * np.log10(freqs + 1e-10)  # Avoid log(0)
        freqs += self.weightings
        freqs = np.clip(freqs, 0, None)
        return freqs

    def _output_result(self, freqs):
        bins = self._get_bin_freqs()
        #analyzer(bins, freqs)
        bass_beat(bins, freqs)

    def _get_bin_freqs(self):
        all_bins = np.concatenate((
            np.linspace(20, 80, 80),
            np.linspace(100, 1000, 100),
            np.linspace(1000, 20000, 100)
        ))
        return all_bins

    #TODO:
    def look_for_transients(self):
        # grab previous windows equal in duration to ~10ms (or some length derived from the frequency range)
        # calculate sharpest salient slope of amplitude
        # calculate variance of dominant frequency
        # if slope and variance are greater than threshold, mark a transient to monitor until full decay / new transient in frequency
        pass

    def attempt_recovery(self):
        if self.failures >= self.max_failures:
            print("3 buffer processing fallbehinds. Using easier hop size.")
            self.hop_size = 1024
            self.failures = 0
        else:
            print("Dynamizer falling behind! Attempting recovery by clearing buffer.")
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

