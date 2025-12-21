# Left off at refactoring into classes
#TODO: Add back in the handling of the 2 signals we currently have, get new refactored code running like it did before. Then go through and give everything a decent name

import socket
import time
from collections import deque

WLED_HOST = "wled-bfn.local"
WLED_PORT = 21324
LISTEN_TIMEOUT_SECONDS = 2

class LightBuffer:
    def __init__(self, num_leds, blend_amount=6):
        self.buffer = deque(maxlen=num_leds)
        self.blend_amount = blend_amount

    def handle_signal(self, signal):
        intensity = self.calc_intensity(signal)
        blended_intensities = self.blend_signal(intensity)
        self.buffer.appendleft(blended_intensities)

    def blend_signal(self, intensity):
        result = []
        prev_value = self.buffer[0] if len(self.buffer) > 0 else [0, 0, 0]
        target_value = [min(intensity, 30), 1, 1]
        for i in range(self.blend_amount):
            blend = (i + 1) / self.blend_amount
            blended = [
                int(prev_value[j] * (1 - blend) + target_value[j] * blend)
                for j in range(3)
            ]
            result.append(blended)
        return result

    def build_frame(self):
        frame = [self.buffer[i] for i in range(min(len(self.buffer), 50))]
        frame.reverse()
        frame.extend(reversed(frame))
        flattened = [ c for sublist in frame for c in sublist ]
        return flattened 

    @staticmethod
    def calc_intensity(signal):
        return (signal//125)**2 + 1

light1 = LightBuffer(100)
buffer2 = LightBuffer(100)

class WLED:
    def __init__(self):
        self.host = WLED_HOST
        self.port = WLED_PORT
        self.num_leds = 100
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        
        self.max_send_rate_hz = 250
        self.min_send_interval = 1.0 / self.max_send_rate_hz
        self.last_send_time = 0

        self.resolve_address()

    def resolve_address(self):
        try:
            self.resolved_address = (socket.gethostbyname(WLED_HOST), WLED_PORT)
        except socket.gaierror:
            self.resolved_address = (WLED_HOST, WLED_PORT)


    def send(self, light, signal):
        if not self.ready_to_send:
            return

        data = bytearray()
        data.append(LISTEN_TIMEOUT_SECONDS)

        light.handle_signal(signal)
        frame = light.build_frame()

        data += bytes(frame)

        #SECOND LOOP

        #buffer = buffer1
        #signal = signal1

        #intensity = max(signal - 15, 0)
        #intensity = intensity // 400
        #intensity = intensity**2 + 1


        #prev_value = buffer[0] if len(buffer) > 0 else [0, 0, 0]
        #target_value = [1, min(intensity, 255), min(intensity//2, 255)]

        #for i in range(5):
            #blend = (i + 1) / 5.0
            #blended = [
                #int(prev_value[j] * (1 - blend) + target_value[j] * blend)
                #for j in range(3)
            #]
            #buffer.appendleft(blended)

        #frame = [buffer[i] for i in range(min(len(buffer), 50))]
        #frame.reverse()
        #frame.extend(reversed(frame))

        #flat = [ c for sublist in frame for c in sublist ]

        #data += bytes(flat)

        try:
            self._socket.sendto(data, self.resolved_address)
            self.last_send_time = time.time()
        except BlockingIOError:
            pass

    @property
    def ready_to_send(self):
        current_time = time.time()
        if current_time - self.last_send_time < self.min_send_interval:
            return False
        return True

#buffer1 = deque(maxlen=num_leds)
#buffer2 = deque(maxlen=num_leds)

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.setblocking(False)


