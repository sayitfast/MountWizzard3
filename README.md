# MountWizzard3 <img src="docu/pics/mw.png" width='64' height='64'/>

#### Application for use in 10micron Mount environment
Supports SGPro, INDI Framework, MaximDL (limited to imaging), Stickstation, MBox, UniHedron SQR, OpenWeather
and some more ASCOM parts. For plate solving I recommend using the new local astrometry.net installation from Jussi
(https://github.com/Jusas/astrometry-api-lite). It works great and you have a blind solver as well on board.

(C) Michael Würtenberger 2018

#### Version release: new, test version actual 3.0 beta 7

[Link to the extended documentation and handbook of MountWizzard3](./docu/home.md)

[Link to FAQ](./docu/FAQ.md)

## Features:
- Runs multi platform (Windows7,10, Linux, Mac OSX)
- Imaging Software: Sequence Generator Pro, INDI are supported. Please refer to their homepages for use.
- Plate Solving Software: PinPoint, SGPro, Astrometry.net (see Jussi's astrometry-api-lite for linux and windows)
- Generate model point based on various algorithms (grid, manual, greater celestial circles, track path)
- Show, save, reload, optimize model (even when model was done manually)
- Auto refraction update if weather station is available for pressure and temperature to mount
- A lot of settings of mount visible and changeable (no need for virtual handcontroller)
- Define up to 6 mount positions, which could be slew directly (e.g. flat panel, check ccd etc.)
- Getting data from open weather (API key needed) and Stickstation
- Direct IP connection to mount. High performance for getting / setting data.
- Analyse modeling data with separate plots.
- Hemisphere window for edit / load / save model points
- Hemisphere window for edit / load / save horizon mask
- Direct slew mount to any az/alt position with mouse click
- Shows and selects alignment star out of handbook
- Make single or continuously Images and solve them.
- Supports KMTronic Relay Box
- Remote shutdown of App for remote site automation
- Boots mount via ethernet WOL if in the same subnet
- Update UTC data / asteroid ... elements (Windows only)
- Audio output for end of slewing / modeling / emergency stop
- No need for configuring the driver and or changing setting refine modes of mount (MW3 does it directly)

Please check for these features, if you have the right (mostly newest) firmware installed on your mount.

### Some videos if you are interested in as sneak preview.
These video might be based on earlier versions.

Doing the preparation before model build: https://www.youtube.com/watch?v=pHFttUJakQo

Dealing with settings: https://www.youtube.com/watch?v=fcdJO7XkqmQ

Optimizing the model: https://www.youtube.com/watch?v=B5rfG7dVWI0

Building an initial model: https://www.youtube.com/watch?v=o7ngZ41EOoM

Building a full model with 43 points: https://www.youtube.com/watch?v=e3NhdaUoqzU

Normal work: building initial and full model (60 points): https://www.youtube.com/watch?v=3lEEv7ltzAg

Building a full model with 100 points: https://www.youtube.com/watch?v=9_uuu0EPdo8

Working with profiles: https://www.youtube.com/watch?v=xOzVaHvTlpU

How to work on Mac OSX: https://www.youtube.com/watch?v=S0dD-xz1EuY

How to work on Linux Ubuntu 16.04: https://www.youtube.com/watch?v=y_rMOMVq75c&t=6s

Working with the hemisphere window: https://www.youtube.com/watch?v=p4RyNgBaO3Y

Working with windows sizing: https://www.youtube.com/watch?v=y77wqqbiG7Q

Installation on linux:

Installation on Mac OSx:

Using the INDI framework:

### Finally
The use this software is at your own risk! No responsibility for damages to your mount or other equipment or your
environment. Please take care yourself !

Hope this makes fun and helps for your hobby, CS Michel
