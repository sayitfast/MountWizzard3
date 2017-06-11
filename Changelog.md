# Changelog
2.3.15
- bugfix for ascom platform discovery

2.3.14
- refactoring device classes (mount, dome)
- adding some data to modeling plot window
- extended logging on console version

2.3.13
- bugfix for command :CMS#  sometimes star added, but return value is E# which show star could not be added ??? added logging to clearify this

2.3.12
- added english support for updater uploads
- added comets / asteroids filter function

2.3.11
- support for MaximDL

2.3.10
- bugfix for camera status

2.3.9
- optimized GUI
- improved error handling and logging for stickstation

2.3.8
- added more robustness in mount connection due to timeouts of non known commands

2.3.7
- robustness against older firmware variants
- horizon mask and minimum setting could now be used additionally

2.3.6
- refactoring get alignment data
- changed text for output startup
- refactoring imaging applications
- added starting imaging apps
- added seeking available imaging apps
- added automatic camera connection
- improved gui for camera (grey / red / yellow / green)
- usage MW without camera app

2.3.5
- try to avoid change font sizes

2.3.4
- bugfix retrofitting model

2.3.3
- bugfix alignment model

2.3.2
- changed working directory for updater to remove local files and to make it work with new updater again

2.3.1
- UTC Data expiration date added under setting / updates
- added getain command to model management

2.2 RC
- release candidate

2.1.32
- robustness for config loading

2.1.31
- bugfix for loading parameters

2.1.30
- bugfix due to feedback from Tom

2.1.29
- bugfix for readme and installer

2.1.28
- refactoring of config management, new parameters should not lead to a message config.cfg could not be loaded
- adding debug output to EXE installer

2.1.27
- bugfix for IP connection topic of TOM
- status sky quality is up

2.1.26
- unihedron SQR support (Ascom driver from SGPro forum necessary)
- Improved gui

2.1.25
- improved gui for orbit data
- improved speed for automation of updater

2.1.24
- large refactoring
- implemented direct mount connection
- improved GUI
- automatisation for orbit and UTC parameters (experimental)

2.1.23
- bugfix platesolve & sync

2.1.22
- bugfix for logger

2.1.21
- added download feature for various download parts

2.1.20
- first set for a pyinstaller
- omit bad values for pressure and temp if obscond doesn't work
- generate actual model from download if the is no model available

2.1.17, 2.1.18, 2.1.19
- bugfix for package location

2.1.16
- changing the packaging behaviour
- reduced size
- explicit reference image for simulation
- preparation for single .exe distribution

2.1.15
- another bugfix

2.1.14
- bugfix error reported from Barry

2.1.13
- added polar plot to model optimization
- auto saving mount models and model data according to workflow
- improved optimization (still cancel capability is missing - > just raise the target rms stops it right now)
- automatic model clear when doing new base model (checkbox)
- you can reuse and extend a refinement model (checkbox)
- calculation original ALT / AZ coordinates from downloaded mount model

2.1.12
- adding save of base / refinement of last model run for model analyses and optimizing
- refactoring model handling in mount
- adding plate solve and sync mount model

2.1.11
- updates from julien to TSX implementation

2.1.10
- changed matplotlib integration from pyplot to figure. this enables multi window solution with plots
- suppressed the unnecessary warning of not found visual c runtime

2.1.9
- first bugfix for missing analyse window

2.1.8
- bugfix save load DSO01 / DSO02 model : didn't do anything
- extending messages to main window
- adding imaging popup for use with ASCOM Cameras
- image widget with zoom and strech for pictures
- changed modeling behaviour for all: first base then refine in separate steps
- auto save base model and refinement model in mount und referenced names
- added color schemes for image view
- added automatic image show, if ascom camera is used
- model point could be generated without having a camera connected

2.1.7
- bugfix

2.1.6
- refactoring interface to imager and solver for ascom, sgpro and theskyx

2.1.5
- added more names for model save in mount
- added two more mount park positions
- added state ready for autorefraction

2.1.4
- bugfix for hints

2.1.3
- bugfix for subframe

2.1.2
- adding ascom camera

2.1.1
- enabled storing status TSX interface
- changing camera status. for green the SGPro / TSX server have to be there and connected !

2.1.0
- added timeshift for DSO track
- optimized GUI for model management
- adding meridian limit for tracking
- adding meridian limit for slewing
- adding time to meridian in gui
- added support for TheSkyX as experimental trial !!!!!

2.0.7
- bugfix subframe handling from tonk

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