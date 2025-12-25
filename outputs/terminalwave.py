from processors import AdaptiveThreshold

class SignalAnalyzer():

    def __init__(self, output_width=100):
        self._threshold = AdaptiveThreshold(decay_rate=1)
        self._output_width = output_width

    def send(self, signal):
        self._threshold.track(signal)
        ceiling = self._threshold.current + .00000000000001
        #print(f"{signal}  ({ceiling} {self._output_width})")
        print("*" * int((signal / ceiling) * self._output_width))


def FrequencyAnalyzer(bins, freqs):
    res = ""
    for i in range(0, len(freqs), 2):
        strength = int(freqs[i])
        if strength > 25:
            res += f"{strength % 100:1.0f} "
        else:
            res += " ."
    print(res)

