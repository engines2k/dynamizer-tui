# Dynamizer
A real-time music feature detector and event server.

### Roadmap
- x Terminal spectral analyzer from real-time signal
- x Basic audio analysis and lookback buffer
- x Reliable kick detection function
- Reliable transient detection function for any frequency range
- Overall loudness / energy function
- Event bus for outputs, server feature
- Implement all outputs listed below
- Compatibility with WLED and other lighting software

### Todo
- SignalAnalyzer: Add the option to 

### Outputs
Dynamizer will produce all the following outputs:
- low_energy
- mid_energy
- high_energy
- beat_kick
- beat_tom
  - OR beat_kick_hz
- beat_snare
- beat_hate
- buzz
- warmth
- chaos
- energy
- beat_density
- brightness
- mood_state
  - Computed based on the previous non-beat related outputs. For example, high energy + high beat_density + high chaos = aggressive

### Goal / Info (kinda old)

The goal for this project is to create a sound-based, general-purpose 'controller' that can broadcast events based on percussive (/ harmonic) music information in real-time. This could then be used to control a music visualizer or a lighting system. This controller would discriminiate between different types of percussive sounds (kick vs snare) as well as different instruments and sounds (hi-hat 1 vs. hi-hat 2). These would then be able to be mapped to different outputs, which could then perhaps control a splash of color or contrast in a music visualizer, or the color or brightness of an element in a lighting system. Ideally this controller will include outputs that change value based on the harmonic content of the song., or even from the overall current loudness or energy of the song. For example, an output will grow in strength, say from a value of 0 towards 1 based on the pitch / volume of the bass, or even from the overall current loudness or energy of the song.

At the moment, simple onset detection of transients seems like the best way to detect these percussive events in real time. HPSS seems like a good idea in theory for processing transients as well, but I will have to develop this project for a while to see if it actually is useful or necessary. At the moment I suspect that this is probably an expensive operation and would hinder real-time processing.

A machine learning approach sounds like it would be more robust and possibly have a wider application outside of this narrow band of MIR, but I don't have the expertise in ML or the traning data neccessary to explore this option. Perhaps an idea for a second version, if I can get this first one off the ground.

- At the moment, this seems like a decent system for handling real-time audio:
    * Get input as a window from stream of ~50ms of audio
    * Analyze for transient onset events
    * Categorize events into type / channel based on frequency.
    * Push event into emit queue, or play immediately. This would result in a delay of the window size plus whatever compute time, ideally minimal.
    * Update longer-term data like bass notes, loudness, song dynamics etc. based on harmonic information
