# MountWizzard3 <img src="docu/pics/mw.png" width='64' height='64'/>

#### Application for use in 10micron Mount environment
Supports SGPro, INDI Framework, MaximDL (limited to imaging), Stickstation, MBox, UniHedron SQR, OpenWeather
and some more ASCOM parts
(C) Michael Würtenberger 2016, 2017, 2018

#### Version release: new, test version actual 3.0 beta 1

[Link to the extended documentation and handbook of MountWizzard3](./docu/home.md)

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

### Finally
The use this software is at your own risk! No responsibility for damages to your mount or other equipment or your
environment. Please take care yourself !

Hope this makes fun and helps for your hobby, CS Michel
