import time
from collections import deque

class DelayQueueItem():
    def __init__(self, data):
        self.data = data
        self.created = time.time()*1000

class DelayQueue():
    def __init__(self, delay=0):
        self._delay = delay
        self._queue = deque()

    def push(self, item):
        self._queue.appendleft(DelayQueueItem(item))

    def get_ready_items(self):
        result = []
        current_time = time.time()*1000
        not_ready = deque()

        # Separate ready items from not-ready items
        while self._queue:
            item = self._queue.pop()
            item_ready_time = item.created + self._delay
            if item_ready_time <= current_time:
                result.append(item.data)
            else:
                not_ready.appendleft(item)

        # Put not-ready items back in the queue
        self._queue = not_ready
        return result

