Feature postponed:
- check TSX

Features new:
- check for southern hemisphere and latitudes < 0
- show directions how to turn know for polar alignment
- moon

Features fine tuning:
- setting site parameters
- more set buttons for config in gui
- GUI: make the main screen nicer: smaller load save, move icon to the left, extend save quit for full text again

- TLE features with full test coverage. Make I/O to top to be testable. write mocks.
- TLE widget should have two pictures. one ist the world with own origin as center, one alt/az for local visibility
- TLE framework should run without widget to be opened.
- make download of TLE data through skyfield and manage update process
- show epoch of tle data and show if its outdated or reload it automatically. manual update should be possible as well.
- update of data updates all charts immediately
- establishing separate timer for satellite updates in satellite widget and make them run only when visible
- using skyfield as well for twilight, moon in hemisphere window
- draw earth with http://milesbarnhart.com/portfolio/python/python-3d-satellite-orbital-trajectory-simulation/
- draw orbits with https://github.com/Elucidation/OrbitalElements/blob/master/graphics.py

- modeling should work out of the box. try to get a wizzard friendly config. test one image and try to set the config
  accordingly. this means binning, focal length, ccd size, settling time, exposure time, test internet connectivity, test
  api key of solver, test version of mount firmware, gain setting and download speeds.

- tests for hysteresis and time flexure should be run only with 3 star model or better non model. therefore blind solving
  is necessary
- more possible tests for flexures and mis alignments, or pictures for explaining.
- using the skyfield framework for satellites
- moving the regular tasks like pressure updates, temp updates, alt az for pointer from mount medium to separate timer

- give some hints for used software in disclaimer
- parsing tle data now moves to skyfield. technical data should be hidden now.

- make mount threads depending on a single class and replace the standard methods in it.
- make the code more readable with pep-8
- move align stars in hemisphere and their updated to a matplotlib animation
- move calculation of alignment stars from mount to align stars

- coding: use continue mor often in iterators and for steps.
- coding: no file names in calls, but the file handle
- coding: no test if key in dict exists, but use a single .get with default for it. should be applied in init_config
- coding: make setter and getter in class instead of direct access. this applies to data dict in mount and elsewhere
- coding: put gui topics to gui thread and the widgets, other stuff out of the threads.
- coding: for block in iter(fread.... raymond hettinger

- make from mount separate module. no gui or link to app be present. move thread building to module itself,
- replace message queue with defined signal.
- define dedicated api how to work with mount, model and widgets.
- go to max length of 79 characters.
- use else statement in for, while
- else statement in try will be executed when no exception occurs.
- finally will be called in any case also when return an other statements are made.
- locks, do that using with lock...

- make a central class for qthread s and on derivative from it for threads with networking. pyqt->thread->thread plus network.

- Loader from skyfield (make a gui entry fro reloading the data or not. verbose = false always, store in config.):
    But users can also create a `Loader` of their own, if there is
    another directory they want data files saved to, or if they want to
    specify different options.  The directory is created automatically
    if it does not yet exist::
        from skyfield.api import Loader
        load = Loader('~/skyfield-data')
    The options are:
    ``verbose``
      If set to ``False``, then the loader will not print a progress bar
      to the screen each time it downloads a file.  (If the standard
      output is not a TTY, then no progress bar is printed anyway.)
    ``expire``
      If set to ``False``, then skyfield will always use an existing
      file on disk, instead of expiring files that are out of date and
      replacing them with newly downloaded copies.

- what is the minimum requirement of mw3.1 ? -> omit FW dependencies
- move Command String out of commandStart to variables
- move parsing return string out of handle ready read and make the rest commodity
- make the FW check and the capabilities once when started.
- this might be also the right time to check weather to mount could communicate. so command would be the first one
   and the special one, too

- persistent data stored with pickle. should be dicts with the data for plotting. saving them on a regular base.


Problems:


