from processors import AdaptiveThreshold

__all__ = ["bass_beat", "snare_beat"]

def bass_beat(bins, freqs):
    threshold = 100
    min_hz = 30
    max_hz = 220
    low_freqs = freqs[(bins > min_hz) & (bins < max_hz + 1)]
    return sum(low_freqs)

# so far, decay rate of 2000 and raise factor .2 is decent for snare type transients
#threshold = AdaptiveThreshold(decay_rate=120000, raise_factor=.1, floor=7)

def snare_beat(bins, freqs):
    min_hz = 3000
    max_hz = 20000
    high_freqs = freqs[(bins > min_hz) & (bins < max_hz + 1)]
    return sum(high_freqs)

    #threshold_crossed = threshold.track(high_db)
    #current = int(threshold.current)
    #if current < len(res):
        #res = res[:current//10] + "---" + res[current//10:]
    #if high_db > current:
        #return str(current) + " " + str(high_db) + res

    #else:
        #return("")

