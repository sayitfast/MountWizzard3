# Changelog:
## beta Version:
0.92
-

0.91
- improved modeling settings / behaviour

0.90
! seetings ar now under /config subdirectory !
if you want to reuse you config, just copy is there !
- save / restore window position for next start
- adding model analysis first step to test
- added coloring for mount status
- added modeling support for pointcloud generation
- added automatic anaysis file naming an storing
- added colored analysis figures
- many corrections and bugfixes

0.89
- bugfixing

0.88
- testing with out camera optimized
- added ISO settings
- added setting for trascking on/off after alt/az slew
- loglevel to debug

0.87
- bugfix und maintenance

0.86
- added canceling of modeling task
- added coloring for running task, so everybode can see, if tasks run
- implementing logfile (model.log), actual on debug level
- improved reconnection to mount

0.85
- transfer mount site data to astropy loc
- reverse calculation of model point in az/alt (actualy removed)
- gegeration of model star setups including visualisation
- updating GUI

0.84
- refactoring -> SGPro abstraction to seperate class

0.83
- optimizing main loop 

0.82
- started implementing logging function
- bugfix for error cases plate solving through SGPro
- stability improvments
- optimizing GUI (Moving Control to Pointing Tab)

0.81
- first running modelling for test
- refactoring coordinate transformations to astropy (and away from driver)

0.8
- Comand tools should work
- base modeling works
- refinement modeling
- Opimizing for Target RMS works


alpha versions:

1.8
- cleanup and remove dependency from comtypes and moving to dynamic late binding of ASCOm Drivers
- If Connection goes away, this could no longer be detected
- no installation of comtypes needed anymore

1.7
- cleaup and doing the modelling with SGPro run. modeling should be possible on an beta status

1.6
- complete refactoring and moving towards multi threading of the tool.
- need to install some more libraries.

1.5
- adding SGPro support and moving towards modelling feature - still nonfunctional

1.4
- including astropy for FITS handling and doing the interface to SGPro
- cleanup, refactoring and readability of code

1.3
- optimizing UI for switching on / off dual tracking, refraction, unattended flip
- improving readme for installation 

1.2
- Bugfixing Refractor Data
- New Feature: Direct Transfer Refraction Data from Stick to Mount by button press

1.2
- minor optimisations

1.0
- initial release