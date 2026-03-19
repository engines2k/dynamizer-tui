import time
from typing import List, Callable
from analyzers import BeatHarmonySeparator
import outputs
from outputs.abstract_analyzer import AbstractAnalyzer
from audio_connectors import JACKConnector
from weightings import a_weighting
from lookback import Lookback
import numpy as np
from scipy.signal import ZoomFFT

__all__ = ["masteranalyzer"]

class MasterAnalyzer():
    max_failures = 3
    sample_rate = 44100
    sample_d = 1 / sample_rate
    window_size = 4096
    hop_size = 64
    lookback_duration_ms = 40
    min_callback_interval_ms = 33
    _active = False

    def __init__(self):
        self._failures = 0
        self._inbuffer = np.array([])  # Initialize as empty 1D array
        self._pause_processing = False
        self._callbacks: List[Callable] = []
        self._last_callback_time = 0.0
        self.audio_connector = JACKConnector(self._process_callback)
        self.signal_lookback = Lookback(self.lookback_duration_ms, self.sample_rate, self.hop_size)
        self._sensitivity = 1.0

        self._signal_windower = np.hanning(self.window_size)
        self._init_fft()
        self._init_outputs()
        self._init_processors()

    def _init_fft(self):
        self.low_zoom_fft = ZoomFFT(self.window_size, [20, 100], 80, fs=self.sample_rate)
        self.mid_zoom_fft = ZoomFFT(self.window_size, [100, 1000], 100, fs=self.sample_rate)
        self.high_zoom_fft = ZoomFFT(self.window_size, [1000, 20000], 100, fs=self.sample_rate)
        #TODO: Change this later to be dynamic along with the FFT strategy.
        self._freq_bins = np.concatenate((
            np.linspace(20, 80, 80),
            np.linspace(100, 1000, 100),
            np.linspace(1000, 20000, 100)
        ))
        self.weightings = self._calc_a_weighting()

    def _init_outputs(self):
        self.outputs = {
            "wled": outputs.wled.WLEDClient(),
            "terminalwave": outputs.SignalAnalyzer('kick_signal'),
        }

    def add_output(self, label: str, output: AbstractAnalyzer):
        self.outputs[label] = output

    def subscribe(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def _init_processors(self):
        self._analyzers = {
            'kick_beat_harmony': BeatHarmonySeparator(
                self.signal_lookback,
                floor=3000,
                min_freq=30,
                max_freq=220,
                label='kick',
                beat_attack=100,
                beat_decay=30
            ),
            'snare_beat_harmony': BeatHarmonySeparator(
                self.signal_lookback,
                min_freq=3000,
                floor=350,
                label='snare'
            ),
        }

    @property 
    def active(self):
        return self._active

    def _calc_a_weighting(self):
        return np.array([a_weighting(freq) for freq in self._freq_bins])

    def activate(self) -> None:
        self.audio_connector.activate()
        for output in self.outputs.values():
            output.activate()
        self._active = True

    def set_sensitivity(self, n_sense: float) -> float:
        self._sensitivity = max(0, min(2, n_sense))
        return self._sensitivity

    def _process_callback(self, n_frames: int) -> None:
        if not self._pause_processing:
            self._process_frames(n_frames)

    def _process_frames(self, n_frames: int) -> None:
        if len(self._inbuffer) > self.sample_rate // 4:
            self.attempt_recovery()

        self._load_frames_into_buffer()

        while self._buffer_ready():
            self._process_buffer_window()

    def _load_frames_into_buffer(self) -> None:
        #TODO: Support for stereo (2 buffers)
        frame = self.audio_connector.get_buffers()[0]  # Fixed: removed ._client
        if frame is not None:
            frame = np.multiply(self._sensitivity, frame)
            self._inbuffer = np.concatenate((self._inbuffer, frame))


    def _buffer_ready(self):
        return len(self._inbuffer) >= self.window_size

    def _process_buffer_window(self):
        window = self._inbuffer[:self.window_size]
        self._inbuffer = self._inbuffer[self.hop_size:]
        freqs = self._analyze_signal_window(window)
        features = self._analyze_freqs_features(freqs)
        self._output_result(features)
        self.signal_lookback.push(freqs)

    def _analyze_signal_window(self, x):
        x = self._apply_window_function(x)
        freqs = self._apply_fft_strategy(x)
        freqs = self._transform_freqs(freqs)
        return freqs

    def _analyze_freqs_features(self, freqs):
        features = {}
        for analyzer in self._analyzers.values():
            feature_set = analyzer.analyze(self._freq_bins, freqs)
            features.update(feature_set)
        return features

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
        freqs = np.clip(freqs, a_min=0, a_max=None)
        return freqs

    def _output_result(self, features):
        current_time = time.time() * 1000
        for output in self.outputs.values():
            output.send(features)
        if current_time - self._last_callback_time >= self.min_callback_interval_ms:
            self._last_callback_time = current_time
            for callback in self._callbacks:
                callback(features)

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
        self._inbuffer = np.array([])  # Reset to empty 1D array
        time.sleep(.5)
        self.toggle_pause()


    def toggle_pause(self):
        self._pause_processing = not self._pause_processing
        status = "PAUSED" if self._pause_processing else "RESUMED"
        print(f"\nProcessing {status}")

masteranalyzer = MasterAnalyzer()


