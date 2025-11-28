import time

class AdaptiveThreshold():

    threshold = 0
    last_time = time.time()

    def __init__(self, decay_rate, raise_factor=1.0):
        self.decay_rate = decay_rate
        self.raise_factor = raise_factor

    def track(self, amplitude):
        self.decay_threshold()
        if amplitude > self.threshold:
            #old_threshold = self.threshold
            self.update_threshold(amplitude)
            #print(f"threshold reached: {amplitude} > {old_threshold}")
            return True
        return False

    @property
    def current(self):
        self.decay_threshold()
        return self.threshold

    def decay_threshold(self):
        delta = time.time() - self.last_time
        self.threshold = max(0, self.threshold - ( delta * self.decay_rate))

    def update_threshold(self, amplitude):
        self.last_time = time.time()
        self.threshold += max(0, (amplitude - self.threshold) * self.raise_factor)
        #print(f"new threshold: {self.threshold}")
