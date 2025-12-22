import time
import outputs
from weightings import a_weighting
from visualizers import  bass_beat, snare_beat
from lookback import Lookback
from types import SimpleNamespace
from audio_connector import AudioConnector
import numpy as np
from scipy.signal import ZoomFFT, freqs

__all__ = ["dynamizer"]

class Dynamizer():
    max_failures = 3
    sample_rate = 44100
    sample_d = 1 / sample_rate
    window_size = 4096
    hop_size = 64
    lookback_duration_ms = 40

    def __init__(self):
        self._failures = 0
        self._inbuffer = np.ndarray(1)
        self._pause_processing = False
        self._audio_connector = AudioConnector(self.process_callback)
        self._lookback = Lookback(self.lookback_duration_ms, self.sample_rate, self.hop_size)

        self._signal_windower = np.hanning(self.window_size)

        self.low_zoom_fft = ZoomFFT(self.window_size, [20, 100], 80, fs=self.sample_rate)
        self.mid_zoom_fft = ZoomFFT(self.window_size, [100, 1000], 100, fs=self.sample_rate)
        self.high_zoom_fft = ZoomFFT(self.window_size, [1000, 20000], 100, fs=self.sample_rate)
        self.weightings = self.calc_a_weighting()

        self._init_outputs()

    def _init_outputs(self):
        self._outputs = SimpleNamespace(**{
            "wled": outputs.wled.WLEDClient(),
            "low_wave": outputs.SignalAnalyzer(),
            "high_wave": outputs.SignalAnalyzer(),
        })

    def calc_a_weighting(self):
        bin_freqs = self._get_bin_freqs()
        return np.array([a_weighting(freq) for freq in bin_freqs])

    def activate(self) -> None:
        self._audio_connector.activate()

    def process_callback(self, n_frames: int) -> None:
        if not self._pause_processing:
            self.process_frames(n_frames)

    def process_frames(self, n_frames: int) -> None:
        if len(self._inbuffer) > self.sample_rate // 4:
            self.attempt_recovery()

        self._load_frames_into_buffer()

        while self._buffer_ready():
            self._process_buffer_window()

    def _load_frames_into_buffer(self) -> None:
        inports = self._audio_connector.inports
        frame = inports[0].get_array() # type: ignore
        self._inbuffer = np.concatenate((self._inbuffer, frame))

    def _buffer_ready(self):
        return len(self._inbuffer) >= self.window_size + self.hop_size

    def _process_buffer_window(self):
        window = self._inbuffer[:self.window_size]
        self._inbuffer = self._inbuffer[self.hop_size:]
        bins = self._analyze_window(window)
        self._output_result(bins)
        self._lookback.push(bins)

        #self._calculate_features()

    def _analyze_window(self, x):
        x = self._apply_window_function(x)
        freqs = self._apply_fft_strategy(x)
        freqs = self._transform_freqs(freqs)
        return freqs

    def _apply_window_function(self, x):
        return x * self._signal_windower

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
        bass = bass_beat(bins, freqs)
        snare = snare_beat(bins, freqs)
        self._outputs.wled.send(bass, snare)
        #self._outputs.low_wave.send(bass)
        self._outputs.high_wave.send(snare)

    def _get_bin_freqs(self):
        all_bins = np.concatenate((
            np.linspace(20, 80, 80),
            np.linspace(100, 1000, 100),
            np.linspace(1000, 20000, 100)
        ))
        return all_bins

    def _calc_amp_avg(self, frames):
        return np.average(np.average(frames, axis=1))

    def _calc_amp_slope(self, frames):
        frame_amp_slopes = []
        amplitudes = [np.sum(frame) for frame in frames]
        for i in range(0, len(amplitudes)-1):
            frame_amp_slopes.append((amplitudes[i] - amplitudes[i+1]) / 2)
        average_slope = np.average(frame_amp_slopes)

        return average_slope

    def _calc_spectral_flux(self, frames):
        diff = np.diff(frames, axis=0)
        positive_diff = np.maximum(0, diff)
        flux = np.sum(positive_diff, axis=1)
        return flux

    def attempt_recovery(self):
        if self._failures >= self.max_failures:
            print("3 buffer processing fallbehinds. Using easier hop size.")
            self.hop_size = 1024
            self._failures = 0
        else:
            print("Dynamizer falling behind! Attempting recovery by clearing buffer.")
            self._failures += 1
        self.toggle_pause()
        self._inbuffer = np.ndarray(1)
        time.sleep(.5)
        self.toggle_pause()


    def toggle_pause(self):
        self._pause_processing = not self._pause_processing
        status = "PAUSED" if self._pause_processing else "RESUMED"
        print(f"\nProcessing {status}")

dynamizer = Dynamizer()

