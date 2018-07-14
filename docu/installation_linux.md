## Installation of MountWizzard on ubuntu 16.04 / 18.04 linux

Please read the following parts to be sure to make the right steps for the successful installation of
MountWizzard. If you have problems, the right spot where to post messages is the 10micron software
developer forum on: http://www.10micron.eu/forum/viewforum.php?f=18. Please take into account that I'm
doing the software as a hobby and you can't expect the support you will have on paid software :-)

### Installation of python on linux

You need to install python 3.6.5. You can download it from:

https://www.python.org/downloads/release/python-365/

Please follow the procedures as explained.

### Installation of MountWizzard3:

Once you have python on your ubuntu, please open a terminal window and you can install MountWizzard3 with
the command:

<pre> pip3 install mountwizzard3 --upgrade --no-cache-dir </pre>

This brings you the MountWizzard3 package on your computer. There are many more packages MountWizzard3 will use and they are
installed as well with this command. It might take some time.

### Update MountWizzard3

If you would like to update MountWizzard3, please use the same command as for new install (see above). The installer
only puts the new needed stuff on the computer.

### Using MountWizzard3 on ubuntu

As MountWizzard3 is a python package, it is stored in the folder, where all the python site packages are located. This
is a directory you normally don't see and use. To avoid searching for it and having a simple interface for starting some
hints:

For starting MountWizzard3 I made a short script (text) file for myself:

<pre>start_mw.sh</pre>

The content of this file is

<pre>
#!/bin/bash
python3 /usr/local/lib/python3.6/dist-packages/mountwizzard3/mountwizzard3.py
</pre>

What happens in this file ?
- First line tells ubu that it is a script for commands.
- Second line: Calls python3 with the path, where the installer put the MountWizzard3 package and starts the main routine
mountwizzard3.py

After that done correctly, a double click on the script file start_mw.sh will open a terminal window and start MountWizzard3.

[Back to Home](home.md)[Back to Home](home.md)