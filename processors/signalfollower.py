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

