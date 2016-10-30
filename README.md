# Mount Tool

###Python QT5 Widget for use in 10micron Mount environment in combination SGPro / Stickstation and some more ASCOM parts
(C) Michael Würtenberger 2016

## Version 0.92 beta

##Features:
- Blind solve for base points
- Generate model point track for observing objects for modeling along track
- Optimize model (even when not modeled with tool)
- Auto refraction - even when not slewing, checking IDLE times of camera
- A lot of settings of mount visible and changable
- Pointing desplay ra/dec az/alt at the same time
- Define up to 4 mount positions, which could be slew directly (e.g. flat panel, check ccd etc.)
- Getting data from open weather (API key needed) and Stickstation
- Set tracking on/off, set tracking speed Sideral / Lunar / Solar
- Set dual tracking on/off
- Flip mount
- Driver stays always in sync aligns model (no corumption of model through sync)
- Model Analysis with separate plots.

## Usage:
Please setup SGPro as you would image. Please also do som sort of focusing (should be obvious) and test some images before start.
If you would like to speed-up the modeling, please disable in SGPro star analysis. It take 4-5 s per image in addition. So far we have
some sort of misbehaviour of the SGPro API, it doesn't allow for HighSpeed Download, so each picture take 10 secs. I have a QSI690 and 
this cam could make it less than 2 sec. Ken (SGPro Owner) will take care for getting the things right. So far no problem, but take some 
more seconds.
##Remarks
### DSLR
Actually the SGPro API has some problems with DSLR Cam's. It doesn't work out properly. 
### Analytics
Ist just a demo so far. Get some inspiration from Thomas Ackers pictures. Anyhow: Each modeling session ist stored under date/time in a 
subfolder analyse. If this subfolder insn't there, pleas create it. You also can choose and older file under Model-> Analyse to view the plots.
### Run Analyse
It does the same point again you had with base points or refinement. Due to the fact, that during modeling the mount refines, the model changes
each star. With that Dry run withou changing the model you get a true difference between the model and the actual solved images.
So far I had only simulation data to test. I'm waiting for next good skies to check if all went good. If you would like to test it,
please feedback, what do you want to see. It should be no problem to implement it.

## Installation:
You need and actual installation of Python and PyQt and it runs ony under windows. I use Windows10 64 bit. 
### Python
So we start with the installation of Python. Necessary ist python >= 3.5
You will find the download @ https://www.python.org/downloads/ the actual version is v 3.5.2. Please download it and install the package on your computer.
### PyQt
For the Gui I use PyQt5. So you need to install that framework as well. I using verion 5 or higher
You install that framework with the command line as administrator "pip install pyqt5"
### pypiwin32
For using COM drivers e.g. comtypes in an threading environment, you need a function called CoInitialize() for the use.
You install that framework with the command line as administrator "pip install pypiwin32"
### astropy
For having a library for doing astronomical calculations and handling FITS files, there is astropy.
Please download that package to a local folder. You can find it in the website which I showed some lines below. Please take cars about your python (3.5.x) and your windows (32/64bit) version. 
You install that library with the command line as administrator "pip install astropy-1.2.1-cp35-cp35m-win_amd64.whl"
A good source for precompiled whl files could be found at http://www.lfd.uci.edu/~gohlke/pythonlibs/. Please check your Windows version and 32/64 setup.
### Plotting library
For having the plotting for the analyse work, you need to install the library for plotting
You install that framework with the command line as administrator "pip install matplotlib"
### ASCOM Framework
If you didn't already install the ASCOM Framework on you computer for astronomy use, please do so now. 
You will find the download @ http://ascom-standards.org the actual version is 6.2. Please download it and install the package on your computer.
### ASCOM drivers
Please install Per Frejvals 10micron ASCOM driver and if you have the Stickstation as well, please do so with Per Frejval ASCOM Stickstation driver, too. 
Another drive is used: OpenWeather ASCOM driver should be installed. For the first configuration you need an API key from OpenWeather. Please follow the instructions on http://openweathermap.org/api
how to get one.
### Mount Tool itself
Please copy all the files from github to you working directory. This could be done by downloading the ZIP file and expand that to your working directory.
To start the tool, please open a command prompt (window) and type "python mount_main.py". If that work, you will see the Gui of the tool.
If some of the devices are not connected, it might take some time until you get the final status (some 5 seconds). For convenience you can link the mount_main.py with a link in windows and configure 
the behaviour. This feature is standard windows environment, please look in the according windows documentation how to do that.
## Usage:
Choose the settings you would like. Configuration of Ascom Environment could be done via settings
### Remarks for professionals:
The mount_ui.ui file is the PyQt Designer file. If you would like to change designs or rearrangements, you could
customize your gui. Please note: this is a part for developers, which are familiar with python development.
### Finally
The use this software is at your own risk. No responsibility for damages to your mount or other environment.
Please take care yourself !

Hope this makes fun and help, CS Michel
