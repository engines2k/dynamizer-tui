__all__ = ["analyzer", "bass_beat"]

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

