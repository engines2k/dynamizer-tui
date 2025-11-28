import math

from thresholds import AdaptiveThreshold

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
        return(res)
    else:
        return("")

class NormalizedSignalVisualizer():
    signal_max = 0.000001
    max_chars = 10

    def visualize(self, signal, char="*"):
        self.signal_max = max(self.signal_max, signal)
        normalized = signal / self.signal_max
        result = math.ceil(normalized * self.max_chars)

        return result * char

threshold = AdaptiveThreshold(decay_rate=100, raise_factor=.4)

def high_stuff(bins, freqs):
    min_hz = 5000
    max_hz = 20000
    high_freqs = freqs[(bins > min_hz) & (bins < max_hz + 1)]
    high_db = sum(high_freqs)
    threshold_crossed = threshold.track(high_db)

    res = ""
    for i in range(0, int(high_db), 10):
        res += "*"

    current = int(threshold.current)
    if current < len(res):
        res = res[:current//10] + "---" + res[current//10:]
    if high_db > current:
        return str(current) + " " + str(high_db) + res

    else:
        return("")

