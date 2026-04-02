import time

class AdaptiveThreshold():

    def __init__(self,
                 decay: float,
                 start: int=0,
                 floor: int=0,
                 raise_factor: float=1.0,
                 raise_type: str='MULT',
                 debouce_ms:int=15):

        self._decay_rate = decay / 1000 # convert to seconds
        self._raise_factor = raise_factor
        if raise_type not in {'MULT', 'FLAT'}:
            raise ValueError(f'Invalid value "{raise_type} for raise_type, should be FLAT or MULT')
        self._raise_type = raise_type
        self._floor = floor
        self._debounce_timer = 0
        self._debounce_period_ms = debouce_ms
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
