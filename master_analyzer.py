import time
import re
from typing import Dict, List, Tuple
from jack import Port
from analyzers import BeatHarmonySeparator
import outputs
from outputs.abstract_analyzer import AbstractAnalyzer
from weightings import a_weighting
from visualizers import  bass_beat, snare_beat
from lookback import Lookback
from audio_connector import AudioConnector
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
    _active = False

    def __init__(self):
        self._failures = 0
        self._inbuffer = np.ndarray(1)
        self._pause_processing = False
        self.audio_connector = AudioConnector(self._process_callback)
        self.signal_lookback = Lookback(self.lookback_duration_ms, self.sample_rate, self.hop_size)

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
        self._outputs = {
            "wled": outputs.wled.WLEDClient(),
            "terminalwave": outputs.SignalAnalyzer('kick_beat'),
        }

    def add_output(self, label: str, output: AbstractAnalyzer):
        self._outputs[label] = output

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
                label='snare'
            ),
        }

    def get_available_ports(self) -> Dict[str, str]:
        result = {}
        ports = self.audio_connector.available_ports
        valid_ports = [ port for port in ports if self.valid_outport(port) ]
        for port in valid_ports:
            result[self._pretty_port_name(port.name)] = port.name[:-3]
        return result
        

    @staticmethod
    def _pretty_port_name(pretty: str) -> str:
        pretty = re.sub(r':(monitor|output)_\w\w', "", pretty)
        return pretty

    @staticmethod
    def valid_outport(port: Port):
        if ('capture' in port.name or 'playback' in port.name) or ('FL' not in port.name):
            return False
        return True

    @property 
    def active(self):
        return self._active

    def _calc_a_weighting(self):
        return np.array([a_weighting(freq) for freq in self._freq_bins])

    def activate(self) -> None:
        self.audio_connector.activate()
        for output in self._outputs.values():
            output.activate()
        self._active = True

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
        inports = self.audio_connector.inports
        frame = inports[0].get_array() # type: ignore
        self._inbuffer = np.concatenate((self._inbuffer, frame))

    def _buffer_ready(self):
        return len(self._inbuffer) >= self.window_size + self.hop_size

    def _process_buffer_window(self):
        window = self._inbuffer[:self.window_size]
        self._inbuffer = self._inbuffer[self.hop_size:]
        freqs = self._analyze_signal_window(window)
        features = self._analyze_freqs_features(freqs)
        #print(features)
        self._output_result(freqs, features)
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

    def _output_result(self, freqs, features):
        bins = self._freq_bins
        bass = features['kick_signal'] #bass_beat(bins, freqs)
        snare = features['snare_signal'] #snare_beat(bins, freqs)
        kick = features['kick_beat']
        self._outputs['wled'].send(bass, snare, kick)
        self._outputs['terminalwave'].send(features)
        #self._outputs.terminalwave.send(snare)

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

masteranalyzer = MasterAnalyzer()


