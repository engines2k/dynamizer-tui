import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor

from analyzers.atmosphere import AtmosphereAnalyzer
from analyzers.grit import GritAnalyzer
from audioconnectors import AudioConnectorFactory
from analyzers import AbstractAnalyzer, BeatHarmonyAnalyzer, FluxAnalyzer, VolumeAnalyzer
from outputs import AbstractVisualizer, WLEDClient, AmplitudeVisualizer
from channelmanager import ChannelManager, Channel
from scipy.signal import ZoomFFT
from typing import Dict, List, Callable, Tuple
from weightings import a_weighting


class FeatureEngine():
    max_failures = 3
    window_size = 2048
    hop_size = 64
    lookback_duration_ms = 100
    min_callback_interval_ms = 20
    _active = False

    def __init__(self):
        self._failures = 0
        self._pause_processing = False
        self._callbacks: List[Callable] = []
        self._last_callback_time = 0.0
        self.audio_connector = AudioConnectorFactory.create(self._process_callback)
        self._sensitivity = 1.0
        self.sample_rate = 44100
        self.sample_d = 1 / self.sample_rate
        self._analyzers: List[AbstractAnalyzer]
        self._signal_windower = np.hanning(self.window_size)
        self._init_fft()
        self._channel_manager = ChannelManager(
            self.audio_connector.n_channels,
            self.sample_rate,
            self.hop_size,
        )
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
        self.outputs: Dict[str, AbstractVisualizer] = {
            "wled": WLEDClient(self.audio_connector.n_channels),
            "terminalwave": AmplitudeVisualizer('grit', channel=Channel.MID)
        }

    def add_output(self, label: str, output: AbstractVisualizer) -> None:
        self.outputs[label] = output

    def subscribe(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def _init_processors(self):
        self._analyzers = [
            BeatHarmonyAnalyzer(
                self._channel_manager.get_lookbacks(),
                channel=Channel.MID,
                label='kick',
                floor=3000,
                min_freq=30,
                max_freq=220,
                beat_attack=30,
                beat_decay=22,
            ),
            BeatHarmonyAnalyzer(
                self._channel_manager.get_lookbacks(),
                channel=Channel.LEFT,
                label='snare',
                min_freq=2000,
                max_freq=6000,
                mult=1.3,
                floor=400,
                beat_attack=200,
                beat_decay=15,
            ),
            BeatHarmonyAnalyzer(
                self._channel_manager.get_lookbacks(),
                channel=Channel.RIGHT,
                label='snare',
                min_freq=2000,
                max_freq=6000,
                mult=1.3,
                floor=400,
                beat_attack=200,
                beat_decay=15,
            ),
            FluxAnalyzer(
                lookbacks=self._channel_manager.get_lookbacks(),
                label=''
            ),
            VolumeAnalyzer(
                lookbacks=self._channel_manager.get_lookbacks()
            ),
            AtmosphereAnalyzer(
                lookbacks=self._channel_manager.get_lookbacks()
            ),
            GritAnalyzer(
                lookbacks=self._channel_manager.get_lookbacks()
            ),
        ]

    @property 
    def active(self):
        return self._active

    def _calc_a_weighting(self):
        return a_weighting(self._freq_bins)

    def activate(self) -> None:
        self.audio_connector.activate()
        self._channel_manager.reset()
        self._active = True
        for output in self.outputs.values():
            output.activate()

    def _reset_inbuffers(self):
        self._channel_manager.reset()

    def set_sensitivity(self, n_sense: float) -> float:
        self._sensitivity = max(0, min(2, n_sense))
        return self._sensitivity

    def _process_callback(self, n_frames: int) -> None:
        if not self._pause_processing:
            self.process_frames(n_frames)

    def process_frames(self, n_frames: int) -> None:
        if self._channel_manager.buffer_ready(self.window_size):
            self.attempt_recovery()
        self._load_inframes()
        while self._buffer_ready():
            windows, treated_freqs = self._treat_windows()
            self._channel_manager.load_results(windows, treated_freqs)
            features = self._analyze_all_features(windows, treated_freqs)
            self._send_to_outputs(features)


    def _load_inframes(self) -> None:
        frames = self.audio_connector.get_buffers()
        scaled_frames = [np.multiply(self._sensitivity, frame) for frame in frames]
        self._channel_manager.load_frames(scaled_frames)

    def _buffer_ready(self):
        return self._channel_manager.buffer_ready(self.window_size)

    def _treat_windows(self) -> Tuple[Dict[Channel, np.ndarray], Dict[Channel, np.ndarray]]:
        windows_by_channel = self._channel_manager.pop_frames(self.window_size, self.hop_size)
        treated_freqs = {}

        left_window = self._apply_window_function(windows_by_channel[Channel.LEFT])
        right_window = self._apply_window_function(windows_by_channel[Channel.RIGHT])

        with ThreadPoolExecutor(max_workers=2) as executor:
            left_future = executor.submit(self._apply_fft_strategy, left_window)
            right_future = executor.submit(self._apply_fft_strategy, right_window)
            left_fft = left_future.result()
            right_fft = right_future.result()

        treated_freqs[Channel.LEFT] = self._transform_freqs(left_fft)
        treated_freqs[Channel.RIGHT] = self._transform_freqs(right_fft)

        mid_fft = (left_fft + right_fft) / 2
        lside_fft = (left_fft - right_fft) / 2
        rside_fft = (right_fft - left_fft) / 2

        treated_freqs[Channel.MID] = self._transform_freqs(mid_fft)
        treated_freqs[Channel.LSIDE] = self._transform_freqs(lside_fft)
        treated_freqs[Channel.RSIDE] = self._transform_freqs(rside_fft)

        return windows_by_channel, treated_freqs

    def _analyze_signal_window(self, x):
        x = self._apply_window_function(x)
        freqs = self._apply_fft_strategy(x)
        freqs = self._transform_freqs(freqs)
        return freqs

    def _analyze_all_features(self, time: Dict[Channel, np.ndarray], freq: Dict[Channel, np.ndarray]) -> Dict[Channel, Dict[str, float]]:
        channel_features = {}
        for analyzer in self._analyzers:
            analyzer_features = analyzer.analyze(self._freq_bins, freq, time)
            for channel, features in analyzer_features.items():
                if channel in channel_features:
                    channel_features[channel].update(features)
                else:
                    channel_features[channel] = features
        return channel_features

    def _apply_window_function(self, x):
        return x * self._signal_windower

    def _apply_fft_strategy(self, x):
        with ThreadPoolExecutor(max_workers=3) as executor:
            low_future = executor.submit(self.low_zoom_fft, x)
            mid_future = executor.submit(self.mid_zoom_fft, x)
            high_future = executor.submit(self.high_zoom_fft, x)
            low_freqs = low_future.result()
            mid_freqs = mid_future.result()
            high_freqs = high_future.result()
        return np.concatenate((low_freqs, mid_freqs, high_freqs))

    def _transform_freqs(self, freqs):
        freqs = np.abs(freqs**2)
        freqs = 20 * np.log10(freqs + 1e-10)  # Avoid log(0)
        freqs += self.weightings
        freqs = np.clip(freqs, a_min=0, a_max=None)
        return freqs

    def _send_to_outputs(self, features):
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
        self._reset_inbuffers()
        time.sleep(.5)
        self.toggle_pause()


    def toggle_pause(self):
        self._pause_processing = not self._pause_processing
        status = "PAUSED" if self._pause_processing else "RESUMED"
        print(f"\nProcessing {status}")

featureengine = FeatureEngine()


