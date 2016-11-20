# Changelog:

1.06
- dome support
- utc from computer to iso time from mount in fits
- canceled run could be rerun
- some refactoring and bugfixes

1.05
- second fix

1.04
- fix bug reported from Geremia Forino

## beta Version:
0.93
- change distribution to python package format
- changed Jnow / J2000 conversion to ASCOM / NOVAS library

0.92
- improvements an refactoring

0.91
- improved modeling settings / behaviour

0.90
! settings ar now under /config subdirectory !
if you want to reuse you config, just copy is there !
- save / restore window position for next start
- adding model analysis first step to test
- added coloring for mount status
- added modeling support for pointcloud generation
- added automatic analyses file naming an storing
- added colored analysis figures
- many corrections and bugfixes

0.89
- bugfixing

0.88
- testing with out camera optimized
- added ISO settings
- added setting for tracking on/off after alt/az slew
- logging level to debug

0.87
- bugfixing und maintenance

0.86
- added canceling of modeling task
- added coloring for running task, so everybody can see, if tasks run
- implementing logfile (model.log), actual on debug level
- improved reconnection to mount

0.85
- transfer mount site data to astropy loc
- reverse calculation of model point in az/alt (actually removed)
- generation of model star setups including visualisation
- updating GUI

0.84
- refactoring -> SGPro abstraction to separate class

0.83
- optimizing main loop 

0.82
- started implementing logging function
- bugfixing for error cases plate solving through SGPro
- stability improvements
- optimizing GUI (Moving Control to Pointing Tab)

0.81
- first running modelling for test
- refactoring coordinate transformations to astropy (and away from driver)

0.8
- Command tools should work
- base modeling works
- refinement modeling
- Optimizing for Target RMS works


alpha versions:

1.8
- cleanup and remove dependency from comtypes and moving to dynamic late binding of ASCOm Drivers
- If Connection goes away, this could no longer be detected
- no installation of comtypes needed anymore

1.7
- cleanup and doing the modelling with SGPro run. modeling should be possible on an beta status

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
- bugfixing refactor Data
- New Feature: Direct Transfer Refraction Data from Stick to Mount by button press

1.2
- minor optimisations

1.0
- initial release