import socket
import random
import time
from collections import deque

# Your WLED mDNS name or IP
WLED_HOST = "wled-bfn.local"
WLED_PORT = 21324


# Example: Set 30 LEDs to solid blue
num_leds = 100
buffer = deque(maxlen=num_leds)

data = bytearray()

data.append(2)

for i in range(num_leds):
    data += bytes((10, 90, 255))  # R,G,B

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

try:
    resolved_address = (socket.gethostbyname(WLED_HOST), WLED_PORT)
except socket.gaierror:
    resolved_address = (WLED_HOST, WLED_PORT)

sock.sendto(data, resolved_address)
print("Sent!")

max_send_rate_hz = 250
min_send_interval = 1.0 / max_send_rate_hz
last_send_time = 0

def send_to_wled(char):
    global last_send_time

    intensity = max(len(char) - 15, 0)
    intensity = intensity // 15
    intensity = intensity**2 + 1

    current_time = time.time()

    if current_time - last_send_time < min_send_interval:
        return

    data = bytearray()
    data.append(2)

    # Blend with previous value for smoother transitions
    prev_value = buffer[0] if len(buffer) > 0 else [0, 0, 0]
    target_value = [1, min(intensity, 255), min(intensity//2, 255)]

    for i in range(5):
        # Blend factor: 0.0 (mostly previous) to 1.0 (fully new)
        blend = (i + 1) / 5.0
        blended = [
            int(prev_value[j] * (1 - blend) + target_value[j] * blend)
            for j in range(3)
        ]
        buffer.appendleft(blended)

    frame = [buffer[i] for i in range(min(len(buffer), 50))]
    frame.reverse()
    frame.extend(reversed(frame))

    flat = [ c for sublist in frame for c in sublist ]

    data += bytes(flat)

    try:
        sock.sendto(data, resolved_address)
        last_send_time = current_time
    except BlockingIOError:
        pass
