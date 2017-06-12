## <img src="../pics/mw.png" width='64' height='64'/> Documentation for Mountwizzard 2

MountWizzard is a open source software for adding features and functions for astronomers, who are using a 10micron mount.

### Installation
Mountwizzard is written in python. So in the past there was the need to install python an a lot of more packages to
make MountWizzard run. This moved ahead using the PIP installer, which is provided by the python community
(https://packaging.python.org/installing/). But anyway installation wasn't that easy.
Since Julien, who helped me to develop the interface to TheSkyX, proposed to move to pyinstaller,
life for installation get much more easy, because the whole bundle (including the python and all related
packages) comes now as a single EXE file. Many thanks for the development community of pyinstaller: http://www.pyinstaller.org.
It still took some time, and there might still be some problems to solve, so far it works great.

Please look to [installation procedures](10installation.md) for detailed information, what and when to do.

### Overview

To get a first impression after start, please have a look to the windows MountWizzard is using they are shown
in a short [overview](01overview.md).

### Working with Mountwizzard for modeling:
 A first good view on how modeling could be done is on the [Modeling Workflow Chart](02modeling_workflow.md)