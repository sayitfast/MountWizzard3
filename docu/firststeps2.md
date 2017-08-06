## Mount conditions and site conditions

<img src="pics/tab_siteconditions.png"/>

MountWizzard fetches data from the mount computer an a regular base depending on the rate of changes the measurements have.
Some information is pulled just on startup (e.g. the location of the mount), others are fetched more often (pointing). Still
there are some, which change (like temperatures), which hav an intermediate rate about every 10 seconds.

### Area 1 - Mount Informations

The mount tells, which location (in lat, lon, height) it is actually put. Regardless where this data was configured. If you have
done this manually via the handcontroller or automatically via an attached GPS receiver. That's the truth, the mount computer will
calculate with (updated at startup).

In addidion you see the actually local sidereal time (updated once per second)

### Area 2 - Temperature motor driver circuit.

10 micron mounts measure many temperatures in different locations. The only common data is the data for the driver circuit of the
motor drivers (for both axes). You could watch the temperature, which indicates at least some ideas, what's happening inside the
mount computer. Please refer to the mount documentation.


### Area 3 - Refraction correction

<b>"Refraction correction status"</b> is the setup in the mount computer, if refraction is taken into account for all calculations
inside the mount. This should be normally "ON". Still you have the chance to switch it via "I/O" button. It's a setting of your mount!
The mount tells you, which refraction parameter it is currently using, it's the data displayed in area 4, yellow part 3! In the
current example 10.0 degrees C and a pressure of 990 hPa.

<b>"periodic parameter update from mountwizzard"</b> checkbox. If checked, MountWizzard will update the data necessary for refraction
correction to the mount. The data consists of temperature and pressure. The source of the used data is the source which is configured
under [ObsCond in settings](settings2.md). The data of this source is shown in area 4, yellow part 2, just aside of the actual used
data in the mount computer. Ideally the yellow party 2 and 3 should show the same numbers, which means, that the mount computer takes
the actually environment conditions into account. The device, which delivers the ObsCond data should be installed nicely. There are
many explanations out there. In my setup, I use a stickstation, which is on top of my APO.

##### How does MountWizzard update the data ?

If you change parameters during image integration, corrections of the pointing model will be made in the mount computer. This might
lead to movements of the mount introduced by these model changes and as result you get bad images with blurred stars. So mostly
updates go along in a state, where the mount is not tracking. In that philosophy tracking means imaging. If you only have the mount
status (like Per's driver), that's the way to go.

MountWizzard also knows about the camera status. So it will update the parameters still if the mount is in tracking mode, but the
camera is not doing image integration. That's and interesting point, if you go for long sequences without any dither or unguided. In
my setup I've seen situations, where the mount is in tracking status for 5-6 hours constantly. In the classical approach that would
mean, no update during this time.

<b>"push parameters to mount manually"</b> mean to force the parameter update any time. Please take care, that you are not in image
integration state, otherwise as explained you might get bar pictures.

### Area 4 - Environment Conditions

As under Area 3 explained yellow part 2 and 3 show the reference data from the device and the actual used data from the mount
computer. In addition you can configure optionally another source of environment data. This data is shown in yellow part 1. None
of this data is used for any calculations in MountWizzard or the mount computer itself. It's just for information.

[Back to first steps](firststeps.md)

[Back to Home](home.md)