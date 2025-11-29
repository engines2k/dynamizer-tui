from thresholds import AdaptiveThreshold

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
        for i in range(0, int(low_freqs_db-100), 20):
            res += "*"
        return(res)
    else:
        return("")

# so far, decay rate of 2000 and raise factor .2 is decent for snare type transients
threshold = AdaptiveThreshold(decay_rate=120000, raise_factor=.1, floor=7)

def snare_beat(bins, freqs):
    min_hz = 3000
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

