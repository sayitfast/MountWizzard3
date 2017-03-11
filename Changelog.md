# Changelog:
2.1
- added timeshift for DSO track
- optimized GUI for model management
- adding meridian limit for tracking
- adding meridian limit for slewing
- adding time to meridian in gui
- added support for TheSkyX as experimental trial !!!!!

2.0.5, 2.0.6
- adjusting to interface change SGPro release 2.6.17 for CMOS cams

2.0.4
- GTMP1 and GTMP2 show same temperature: 10micron: that's right, because its the temp of the motor circuit. changed that
- removed error message "horizon points file could not be loaded" if filename is empty
- corrected behaviour when changing horizon mask setting and enabling direct redraw
- bugfix to access file model001.py while simulation reported by Steffen (Smayer)
- improved responsiveness for selecting DSO points and Grid points (immediate redraw)


2.0.2, 2.0.3
- bugfix in batch modeling

2.0.1
- improved mounts handling

2.0.0
- added tooltips in analyses window
- added save config button (thanks for the hint BrokeAstronomer)

1.9.3, 1.9.4, 1.9.5, 1.9.6
- rehearsal mode

1.9.2
- message for model clearing

1.9.1
- added customization of DSO Track

1.9.0
- finalizing the release candidate

1.1.16
- bugfix clear model -> thanks to TONK
- refactoring az alt from int to float
- error logging in stick / weather implemented
- improvement readability tracking widget
- bugfix Dome support
- bugfix camera chooser

1.1.15
- added Camera chooser
- refactoring for multiple software support
- refactoring of classes inside mw

1.1.14
- bugfix DSO model point

1.1.13
- small internal bugfixes for gui
- delete worst model point
- bugfix (hopefully) for froze pointer

1.1.12
- for loading model points file, TSX (TheSkyX Format is also supported)

1.1.11
- adding first unittests
- refactoring

1.1.10
- changing setup.py

1.1.9
- changing simulation values

1.1.8
- optimisations
- adding feature batch model calculation

1.1.7
- cyclic logs per day
- correction simulation ascom telescope simulator
- bugfix waiting for start slewing while modeling

1.1.6
- correction relays
- ui improvements
- test automation

1.1.5
- ui refreshment
- change analyse view
- update storing data

1.1.4
- ui reshaping and separate windows for points and analyse
- updating model algorithm for batch calculation
- updating tooltips with correct indications
- bugfixing

1.1.3
- bugfixing

1.1.2
- refactoring windows classes
- refactoring analyse classes
- bugfix barry talked (spelling issue)

1.1.1
- bugfix solve message say OK, but timeout plate solving happened
- bugfix in hint calculation in case of binning
- reshaping logging while modeling
- complete new analyse part
- added polar plots for analysing your modeling
- bugfixing

1.1.0
- release of tested version

1.0.26
- check and change ra/dec hints

1.0.25
- improved storing of coordinate due to bugfix
- optimized interface for load horizon file

1.0.24
- bugfix to reported michel-d bug

1.0.23
- increased precision for model parameter transfer
- DSLR should run with SGPro beta 2.5.2.8

1.0.22
- bugfix modeling

1.0.21
- preparation for batch modeling / remodeling

1.0.20
- improved storing while keeping images from modeling

1.0.19
- bugfix in solving

1.0.18
- optimizing for time delay between imaging and point add in mount

1.0.17
- bugfix for not connecting stickstation directly

1.0.16
- changed waiting for start slewing to avoid a race condition

1.0.15
- setting default installation without dome
- increasing wait time for slewing to 2.2 s

1.0.14
- adaption for Time Flexure -> Delay time
- adding more option for Grid points
- adding hysterese analyse

1.0.13
- turning on tracking while imaging in analyse path
- show dome status in gray, when no dome driver selected
- checked for PlateSolve2: should run
- astronomy.net should work

1.0.12
- correction readme install
- bugfix model run already modeled points

1.0.11
- bugfix in driver selection

1.0.10
- analyse for time dependant deviations of mount
- implemented showing position and movement of dome if present

1.0.9
- removed extended logging

1.08
- bugfixing dome support with Geremia

1.07
- bugfixes dome support

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