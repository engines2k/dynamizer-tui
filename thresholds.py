import time

class AdaptiveThreshold():

    threshold = 0
    last_time = time.time()

    def __init__(self, decay_rate, floor=0, raise_factor=1.0):
        self.decay_rate = decay_rate
        self.raise_factor = raise_factor
        self.floor = floor

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
        self.threshold = max(self.floor, self.threshold - ( delta * self.decay_rate // 1000))

    def update_threshold(self, amplitude):
        self.last_time = time.time()
        self.threshold += max(0, (amplitude - self.threshold) * self.raise_factor)
        #print(f"new threshold: {self.threshold}")
