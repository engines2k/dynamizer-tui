import math

__all__ = ["analyzer", "bass_beat", "NormalizedSignalVisualizer"]

def analyzer(bins, freqs):
    res = ""
    for i in range(0, len(freqs), 2):
        strength = int(freqs[i])
        if strength > 25:
            res += f"{strength % 100:1.0f} "
        else:
            res += " ."
    print(res)

def bass_beat(bins, freqs):
    threshold = 100
    min_hz = 30
    max_hz = 220
    low_freqs = freqs[(bins > min_hz) & (bins < max_hz + 1)]
    low_freqs_db = sum(low_freqs)
    if low_freqs_db > threshold:
        res = ""
        for i in range(0, int(low_freqs_db-100), 30):
            res += "*"
        print(res)
    else:
        print("")

class NormalizedSignalVisualizer():
    signal_max = 0.000001
    max_chars = 10

    def visualize(self, signal, char="*"):
        self.signal_max = max(self.signal_max, signal)
        normalized = signal / self.signal_max
        result = math.ceil(normalized * self.max_chars)

        return result * char
