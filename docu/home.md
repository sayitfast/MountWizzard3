## <img src="pics/mw.png" width='64' height='64'/>Handbook for Mountwizzard3

MountWizzard is a open source software for adding features and functions for astronomers,
who are using a 10micron mount. MountWizzard is written in python and uses some other astronomy
and utility packages (e.g. PyQt5, astropy,...). As python and Qt is available on multiple platforms,
so does MountWizzard. Actually with python 3.6.5 and PyQt 5.11.2 (Qt 5.11.1) you could use
Mountwizzard on Windows, Linux and Mac OS.

The straight forward way of doing the install for experienced users is to have python installed on
your computer and use pip installer for all other things. Since Julien, who helped me to develop the
interface to TheSkyX, proposed to move to pyinstaller, life for installation get much more easy,
because the whole bundle (including the python and all related packages) comes now as a single EXE
file. for windows, which includes. Many thanks for the development community of pyinstaller:
http://www.pyinstaller.org. It still took some time, and there might still be some problems to
solve, so far it works great.The running performance in both cases is the same, but the self
extracting will take some seconds to start.

MountWizzard supports tooltips. So hopefully if you don't get an idea, whats is going to happen,
just put you mouse above a field or button and you will see the tooltip!

### New Features since MountWizzard 2.6
- Support for profiles. Profile store everything which is customizable
- Image making and solving
- Multi Platform support. MountWizzard runs now on Windows, MacOSX and Linux
- Support for INDI framework (CCD, Telescope, Environment)
- Support for Astrometry.Net Solver framework (Local and Online solver)
- Editing / Load / Save of model points and horizon mask
- New processes for model building
- Performance improvements (faster model making)
- Always showing actual model data

### Overview
To get a first impression after start, please have a look to the [main screens and the gui](overview.md)
MountWizzard is using and which windows you will experience from the beginning on.

I wrote down some thoughs about model building on 10micron mounts: [Link to model building](modelbuilding)

### Installation
Please look to

- [installation on windows 7 / 10 with EXE package ](installation_windows.md)
- [installation on ubuntu 16.04 / 18.04 Ubuntu Linux](installation_linux.md)
- [installation on Mac HighSierra](installation_mac.md)
- [installation of other frameworks](installation_other.md)

for detailed information, what and when to do.

### Setting up MountWizzard
All necessary steps for the [configuration of MountWizzard](configuration.md) are explained.

### Setting up my gear
Based on my equipment, i tried to explain what to do for an astronomy imaging setup. There are a lot of
 possibilities to do this and I'm happy about any hint you give me.
 [Stepping through my personal setup](./setup_gear/setup_gear.md)





