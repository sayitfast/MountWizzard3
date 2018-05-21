## <img src="pics/mw.png" width='64' height='64'/>Handbook for Mountwizzard3

MountWizzard is a open source software for adding features and functions for astronomers,
who are using a 10micron mount. MountWizzard is written in python and uses some other astronomy
and utility packages (e.g. PyQt5, astropy,...). As python and Qt is available on multiple platforms,
so does MountWizzard. Actually with python 3.6.5 and PyQt5.10.1 you could use Mountwizzard on Windows,
Linux and Mac OS.

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
- Multi Plattform support. MountWizzard runs now on Windows, MacOSX and Linux
- Support for INDI framework (CCD, Telescope, Environment)
- Support for Astrometry.Net Solver framework (Local and Online solver)
- Editing / Load / Save of model points and horizon mask
- New processes for model building
- Performance improvements (faster model making)
- Always showing actual model data


### Overview
To get a first impression after start, please have a look to the [main screens and the gui](overview.md)
MountWizzard is using and which windows you will experience from the beginning on.

### Installation
Please look to

- [installation on windows 7/10 with EXE package ](installation_windows.md)
- [installation on ubuntu 16.04 linux](installation_linux.md)
- [installation on Mac HighSierra](installation_mac.md)
- [installation of other frameworks](installation_other.md)

for detailed information, what and when to do.

### Setting up MountWizzard
All necessary steps for the [configuration of MountWizzard](configuration.md) are explained.
### Setting up my gear
Based on my equipment, i tried to explain what to do for an astronomy imaging setup. There are a lot of
 possibilities to do this and I'm happy about any hint you give me.
 [Stepping through my personal setup](./setup_gear/setup_gear.md)

### Remarks about model building
As there was (and is) ModelMaker from Per in the past (btw which influenced me to buy the right mount)
some more solutions like ModelCreator from Martin happened. I'm doing MountWizzard work the way like I
use it personally, but if there are ideas which should be relized from users side, please let me know.

This said, I follow a different path in modeling for 10micron mount than in the past. There was always the first
step by using 3 base points for the start. There is no reason about that but the fact that you need at least
3 stars to buld a first model to get some information about you polar alignment etc. But there could be even
more of them to get a better picture of your actual setup. Others (like me) use fixed piers with good
markers on it and with the quality of a good model I don't need a frist setup for alignment, I just want
to get a new model.

For that reason I splitted the workflow into two parts: The Initial Model (for the
first use case) and the Full Model (for the second one). Another difference you might discover: I do not
build the model step by step over all the stars, I just make all the slewing work, images and solve in
parallel and than process them to the mount. As you have all the data for a model collected, you could
redo any model making session just with the data already saved on your computer.



