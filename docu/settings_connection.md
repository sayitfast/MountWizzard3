## Settings for imaging and imaging environment connections

<img src="pics/settings_connection_edit2.png"/>

### Area 1: Imaging Application

MountWizzard can use different applications for imaging. But they were used in a package. So you have
to decide your favourite app for doing your astro work. Please setup the application as you would do
for imaging. That means: choose the right equipment of your gear, choose the right devices and profiles.
Take care of connecting the camera, switch on the cooler, set filter and focus.

You have the choice between:
- Sequence Generator Pro
- MaximDL
- INDI Framework
- None (if you just use MountWizzard as frontend to steer your mount, update refraction etc.)

Still to be transparent what happens MountWizzard always image to a FITS file and do plate solving
based on that FITS file. So everything goes over the FITS files.
MountWizzard is able to start your application automatically and also could connect the camera.
A connected camera is shown with a green status (Area 5) at the camera status.

### Area 2: Astrometry setup (plate solving)

You could use different applications for plate solving. Please take care if you mix them with imaging
applications. The could fit, but there is no guarantee for that. You could use:
- Sequence Generator Pro (Plate solcing solution you check in SGP)
- PinPoint (if you have a full version installed - lite from MaximDL is not enough)
- Astrometry.NET
- None

With astrometry.net you could use online as well as local solvers which also includes blind solving.

### Area 3: Environment Setup
Please choose the framework from which you would like to use environmental data:
- INDI
- ASCOM
- None

### Area 4: Dome Setup
Please choose the framework from which you would like to use dome control:
- INDI
- ASCOM
- None


[Back to settings](settings.md)

[Back to first steps](firststeps.md)

[Back to Home](home.md)