import jack
import numpy as np
import time
from itertools import chain

my_samplerate = 44100
my_d = 1 / my_samplerate

client = jack.Client("Visualizer")

client.inports.register("left")
client.inports.register("right")

@client.set_process_callback
def process(frames):

    in_data = client.inports[0].get_array() # type: ignore

    fourier = np.fft.fft(in_data)


    res = ""

    for i in chain(range(1, 6, 2),  range(7, len(fourier.real-50), 13)):
        mag = np.abs(fourier.real[i])  # bin near ~88 Hz
        if i < 5:
            res += " "
        if mag > 3/i*18:
            res += f" {mag:1.0f} "
        else:
            res += " . "
            

    print(res)

@client.set_shutdown_callback
def shutdown(status, reason):
    print("JACK shutdown:", status, reason)

with client:
    client.connect("Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FL", "Visualizer:left")
    client.connect("Scarlett 2i2 3rd Gen Headphones / Line 1-2:monitor_FR", "Visualizer:right")

    print("Visualizer running. Press Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

print("Client closed.")
