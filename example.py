import numpy as np
import sounddevice as sd

duration = 5.5

outputs = sd.query_devices()

print("printing outputs...")
print(outputs)

my_samplerate = 44100
my_d = 1 / my_samplerate

def callback(indata, outdata, frames, time, status):
    for channel in indata:
        channel[0]
    if status:
        print(status)
    outdata[:] = indata

    channel = indata[:, 0]
    fourier = np.fft.fft(channel)
    #n = channel.size
    #freq = np.fft.fftfreq(n, d=my_d)

    # print the value in bin 3 [88hz(?)]
    eight_eight_hz = fourier.real[2]
    if eight_eight_hz > .5:
        print("{:>10.3f}".format(eight_eight_hz))


with sd.Stream(channels=2, blocksize=1000, callback=callback) as stream:
    print(f"Reading from input {stream.device}, with a sample rate of {stream.samplerate} and size of {stream.samplesize}")
    sd.sleep(int(duration * 1000))
