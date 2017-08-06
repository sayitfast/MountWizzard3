## Settings for imaging and imaging environment

<img src="pics/tab_settings_imagingsetup.png"/>

### Area 1: Camera / Plate Solver Application

MountWizzard can use different applications for imaging and plate solving. But they were used in a package. So you have to decide your
favourite app for doing your astro work. Please setup the application as you would do for imaging. That means: choose the right equipment
of your gear, choose the right devices and profiles. Take care of connecting the camera, switch on the cooler, set filter and focus. That
means setting the plate solver of your choice in the application. All of them come with a single or even multiple selection of plate solving
solutions. As said you can't mix it (imaging from the first and plate solving from the second application).

You have the choice between:
- Sequence Generator Pro
- TheSkyX
- MaximDL
- ASCOM (not finished)
- None (if you just use MountWizzard as frontend to steer your mount, update refraction etc.)

Still to be transparent what happens MountWizzard always image to a FITS file and do plate solving based on that FITS file. So everything
goes over the FITS files.
MountWizzard is able to start your application automatically and also could connect the camera. A connected camera and plate solver is shown
with a green status (area 4) at the camera status. You also can start the application and connect / disconnect via the buttons.

### Area 2: Camera Setup
MountWizzard let's you set the camera bin, the exposure time and you can use fast download, if your camera support this read-out mode.
In addition ISO could be set(experimental). For getting sharp pictures please set the settling time of your mount. Normally 1-2 seconds should
be enough. I'm doing 1s even when having max slew rate of the mount.
Next data is for setting up parameters for the plate solver. Starting with the pixel size of your camera and the resulting focal lenght
of your telescope. If your camera supports subframes, you can check it and define the portion of picture (it will be centered) for download.
The checkbox Keep images from modeling allows to keep all FITS files from your model making session. The images are stored in the subfolder
/images in a directory which holds the date and time of the start of the model building session (format: YYYY-MM-DD-HH-MM-SS)

### Area 3: support files for model building.

Mount Wizzard could use a given model points file from Model Maker and will import the data on the fly.

For setting a horizon line in the Modeling Plot Window you can choose a horizon mask file (format is equal to Model Maker setup) or / and
a fixed horizon mask with a dedicated altitude als horizon. You can check both options. In that case MountWizzard just overlays the
information and take both constraints into account.

[Back to settings](settings.md)

[Back to first steps](firststeps.md)

[Back to Home](home.md)