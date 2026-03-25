<a id="readme-top"></a>

<div align="center">
 <!-- Dynamizer -->
<pre>
 ▌         𝅘𝅥      
▛▌▌▌▛▌▀▌▛▛▌▌▀▌█▌▛▘
▙▌▙▌▌▌█▌▌▌▌▌▙▖▙▖▌ 
⸱⸱▄▌⸱•⦁●⦁•⸱⸱⸱⸱⸱⸱⸱⸱
</pre>
</div>

<div align="center">
    <p>A real-time music feature detector and event server.</p>
    <a href="https://github.com/engines2k/dynamizer/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/engines2k/dynamizer/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about">About</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About

Dynamizer is a real-time musical signal analyzer that can drive a multitude of visualizations in many contexts, from terminal spectrum analyzers and WLED audio-reactive lighting setups, to on-the-fly rendered scenes.

There are many options for audio-reactive consumer hardware, but these are often limited by onboard mics and processing, causing delays and inaccuracies that degrade the user's connection between the visual effects and the music being played. The goal of Dynamizer is to provide a low-latency, accurate, and versatile option for those looking for real-time visualizations and lighting effects.

Currently Dynamizer is hard-coded to connect with an WLED controller and 2 strips of lights based on a single channel input, but as it grows it will be expanded to support any user setup, with a graphical interface and dynamic control of mono and stereo inputs, outputs, analyzer settings, and built-in WLED effects.


## Getting Started

You can test the project in its current state by following the steps below.

### Prerequisites

* python

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/engines2k/dynamizer.git
   ```
2. Install Python packages
   ```sh
   cd dynamizer
   pip install -r requirements.txt
   ```
3. Run main.py
   ```sh
   python main.py
   ```

## Contributing

To anyone who would be interested, any contributions would be **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repository and create a pull request. You can also simply open an issue with the tag "enhancement".

Feel free to drop a star if you like.


## License

Distributed under GNU GPL v3. See `LICENSE` for more information.


## Contact

Zeke Barefoot - [@engines2k](https://twitter.com/engines2k) - zekebarefoot0@gmail.com

<p align="right">(<a href="#readme-top">back to top</a>)</p>

