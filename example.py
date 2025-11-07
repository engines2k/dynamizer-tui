import librosa

filename = librosa.example('nutcracker')

y, sr = librosa.load(filename)

tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

print(f"Estimated tempo: {tempo} beats per minute")
