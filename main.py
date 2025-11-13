import jack
import numpy as np
import time

my_samplerate = 44100
my_d = 1 / my_samplerate

client = jack.Client("Visualizer")

client.inports.register("left")
client.inports.register("right")

@client.set_process_callback
def process(frames):
    in_data = client.inports[0].get_array() # type: ignore

    fourier = np.fft.fft(in_data)


    mag = np.abs(fourier.real[2])  # bin near ~88 Hz
    if mag > 10:
        print(f"{mag:10.3f}")
    else:
        print("")

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
