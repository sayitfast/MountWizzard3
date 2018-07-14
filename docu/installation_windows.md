## Installation of MountWizzard

Please read the following parts to be sure to make the right steps for the successful installation of
MountWizzard. If you have problems, the right spot where to post messages is the 10micron software
developer forum on: http://www.10micron.eu/forum/viewforum.php?f=18. Please take into account that I'm
doing the software as a hobby and you can't expect the support you will have on paid software :-)

### Where to find the Application ?

The application as well as this documentation and the distribution itself is hosted on github:

https://github.com/mworion/mountwizzard3-dist.

You will find the readme in the main page, which also directs to the extended documentation. The
interesting part for downloading the application is the subdirectory /dist in github. The page is
looking like the following example and the /dist folder is marked red:

<img src="pics/github_dist.png"/>

If you choose the /dist folder, you could see the application files for download:

<img src="pics/github_dist_files.png"/>

You will normally see 4 application files: there are the released ones (in the example above version v3.0)
and the latest beta version. Please remember that even version numbers (like 2.2.x) are release versions
and uneven numbers (like 2.3.x) are beta ones. For betas in general: please provide detailed feedback
including tests so that it enables others to participate in improving MountWizzard as well.

There are basically two versions of each release: a version which is called mountwizzard_vx.y.z and a
second version called mountwizzard-console_vx.y.z. Both of them share the same functionality. The only
difference is that the console version show in addition to the MountWizzard windows a command window,
where the pyinstaller boot loader writes his output to. So in case you have troubles starting MountWizzard,
please start the console version and save the output of the command window for further investigations.

So the best way is to download both versions (pure and console) to you computer.

#### Reminder: As I am currently not able to offer signed applications, please ensure virus checking on your side for your own safety!
Before I put the application to github they are OK, but you never know.

### Compatibility
Actually the application package (.EXE) is tested and verified to be able to run in win7 and win10
operating systems. Both 32bit and 64bit are supported. The bundle itself contains only 32bit runtime
libraries. Older versions like vista have not been tested successful.
The package file (.tar.gz) is tested in ubuntu 16.04 / 18.04 LTS and Mac OSx High Sierra. On these systems
python 3.6.5 has to be installed manually.

[Back to Home](home.md)