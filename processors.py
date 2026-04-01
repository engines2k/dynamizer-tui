import time
from typing import Optional

class SignalFollower():

    def __init__(self, attack, decay, floor=0, ceil=None) -> None:
        self._attack: int = attack
        self._decay: int = decay
        self._value: int = 0
        self._floor: int = floor
        self._ceil: Optional[int] = ceil
        self._decay_timer: float = time.time() * 1000

    def track(self, signal):
        time_now = time.time()*1000
        rate_limit = self._attack if signal > self._value else self._decay

        rate_factor = rate_limit * (time_now - self._decay_timer) / 1000
        delta_signal = (signal - self._value)
        value_adjust = delta_signal * rate_factor

        new_val = self._value + min(value_adjust, rate_limit)
        bounded_val = max(new_val, self._floor)

        if self._ceil:
            bounded_val = min(self._value, self._ceil)
        self._value = bounded_val

        self._decay_timer = time_now
        return self._value

    @property
    def value(self):
        return self._value
    def _last_decay_delta(self):
        return time.time()*1000 - self._decay_timer



class AdaptiveThreshold():

    def __init__(self, decay_rate, start=0, floor=0, raise_factor=1.0, raise_type='MULT', debouce_ms=15):
        self._decay_rate: int = decay_rate / 1000 # convert to seconds
        self._raise_factor: float = raise_factor
        if raise_type not in {'MULT', 'FLAT'}:
            raise ValueError(f'Invalid value "{raise_type} for raise_type, should be FLAT or MULT')
        self._raise_type: str = raise_type
        self._floor: int = floor
        self._debounce_timer: float = 0
        self._debounce_period_ms: int = debouce_ms
        self._threshold = start
        self._last_time = time.time() * 1000

    def track(self, signal):
        self._decay_threshold()
        amplitude = abs(signal)
        if amplitude > self._threshold and not self._debouncing:
            self._debounce_timer = (time.time() * 1000)+self._debounce_period_ms
            self._set_threshold(self._threshold + self._calc_raise_amount(amplitude))

        return self._threshold
        
    @property
    def _debouncing(self):
        return self._debounce_timer > time.time()*1000

    @property
    def current(self):
        self._decay_threshold()
        return self._threshold

    def _calc_raise_amount(self, amplitude: float):
        if self._raise_type == 'FLAT':
            return self._raise_factor
        return (amplitude - self._threshold) * self._raise_factor

    def _decay_threshold(self):
        current_time = time.time() * 1000
        delta = current_time - self._last_time
        self._set_threshold(self._threshold - (delta * self._decay_rate))
        self._last_time = current_time

    def _set_threshold(self, amplitude):
        self._threshold = max(self._floor, amplitude)
