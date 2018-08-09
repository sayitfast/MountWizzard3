Feature postponed:
- check TSX

Features new:
- check for southern hemisphere and latitudes < 0
- show directions how to turn know for polar alignment
- moon

Features fine tuning:
- setting site parameters
- more set buttons for config in gui
- TLE features with full test coverage. Make I/O to top to be testable. write mocks.
- TLE widget should have two pictures. one ist the world with own origin as center, one alt/az for local visibility
- TLE framework should run without widget to be opened.
- modeling should work out of the box. try to get a wizzard friendly config. test one image and try to set the config
  accordingly. this means binning, focal length, ccd size, settling time, exposure time, test internet connectivity, test 
  api key of solver, test version of mount firmware, gain setting and download speeds.
- blind solving enable for SGPro should be available for initial model only
- tests for hystersis and time flexure should be run only with 3 star model or better non model. therfore blind solving 
  is necessary
- more possible tests for flexures and misalignements, or pictures for explaining.
- using the skyfield framework for satellites 
- moving the regular tasks like pressure updates, temp updates, alt az for pointer from mount medium to separate timer
- establishing separate timer for satellite updates in satellite widget and make them run only when visible
- make download of TLE data through skyfield and manage update process
- show epoch of tle data and show if its outdated or reload it automatically. manual update should be possible as well.
- update of data updates all charts immediately
- give some hints for used software in diclaimer 
- parsing tle data now moves to skyfield. technical data should be hidden now.
- using skyfield as well for twilight, moon in hemisphere window
- draw earth with http://milesbarnhart.com/portfolio/python/python-3d-satellite-orbital-trajectory-simulation/
- orbits zeichnen mit https://github.com/Elucidation/OrbitalElements/blob/master/graphics.py

Problems:


