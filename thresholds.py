import time

class AdaptiveThreshold():

    _threshold = 0
    _last_time = time.time() * 1000

    def __init__(self, decay_rate, floor=0, raise_factor=1.0):
        self._decay_rate = decay_rate / 1000 # convert to seconds
        self._raise_factor = raise_factor
        self._floor = floor
        self._debounce_timer = 0
        self._debounce_period_ms = 20

    def track(self, signal):
        self._decay_threshold()
        amplitude = abs(signal)
        if amplitude > self._threshold and not self._debouncing:
            self._debounce_timer = (time.time() * 1000)+self._debounce_period_ms
            self._set_threshold(self._threshold + (amplitude - self._threshold) * self._raise_factor)

        return self._threshold
        
    @property
    def _debouncing(self):
        return self._debounce_timer > time.time()*1000

    @property
    def current(self):
        self._decay_threshold()
        return self._threshold

    def _decay_threshold(self):
        current_time = time.time() * 1000
        delta = current_time - self._last_time
        self._set_threshold(self._threshold - (delta * self._decay_rate))
        self._last_time = current_time

    def _set_threshold(self, amplitude):
        self._threshold = max(self._floor, amplitude)
