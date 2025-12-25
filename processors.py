import time

class SignalFollower():

    def __init__(self, attack, decay, floor=0, ceil=None) -> None:
        self._attack = attack
        self._decay = decay
        self._value = 0
        self._floor = floor
        self._ceil = ceil

    def track(self, signal):
        rate_limit = self._attack if signal > self._value else self._decay

        new_val = self._value + max(signal - self._value, rate_limit)
        bounded_val = max(new_val, self._floor)

        if self._ceil:
            bounded_val = min(self._value, self._ceil)
        self._value = bounded_val

        return self._value

    @property
    def value(self):
        return self._value


class AdaptiveThreshold():

    _threshold = 0
    _last_time = time.time() * 1000

    def __init__(self, decay_rate, floor=0, raise_factor=1.0):
        self._decay_rate = decay_rate / 1000 # convert to seconds
        self._raise_factor = raise_factor
        self._floor = floor
        self._debounce_timer = 0
        self._debounce_period_ms = 15

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
