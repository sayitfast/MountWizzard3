# MountWizzard

###Python PyQt5 Widget for use in 10micron Mount environment in combination SGPro / Stickstation / OpenWeather and some more ASCOM parts
(C) Michael Würtenberger 2016

## Version 1.07

# Important:
##### I changed the distribution model to python package (makes it a lot easier to install) and the tool got a name: MountWizzard :-)
On GitHub you will find from now on most probably only the package version under 
<pre>https://github.com/mworion/mountwizzard.git</pre>
the older version under 'mount' will disappear !

##Features:
- Blind solve for base points
- Generate model point track for observing objects for modeling along track
- Optimize model (even when not modeled with tool)
- Auto refraction - even when not slewing, checking IDLE times of camera
- A lot of settings of mount visible and changeable
- Pointing display ra/dec az/alt at the same time
- Define up to 4 mount positions, which could be slew directly (e.g. flat panel, check ccd etc.)
- Getting data from open weather (API key needed) and Stickstation
- Set tracking on/off, set tracking speed Sideral / Lunar / Solar
- Set dual tracking on/off
- Flip mount
- Driver stays always in sync aligns model (no model change through sync)
- Model Analysis with separate plots.

## Usage:
Please setup SGPro as you would image. Please also do some sort of focusing (should be obvious) and test some images before start.
If you would like to speed-up the modeling, please disable in SGPro star analysis. It takes 4-5 s per image in addition.

##Remarks

### DSLR
Actually the SGPro API has some problems with DSLR Cam's. It doesn't work out properly. 

### Analytics
Ist just a demo so far. Get some good view from Thomas (thanks for his work). Anyhow: Each modeling session ist stored under date/time in a 
subfolder analyse. You also can choose and older file under Model-> Analyse to view the plots.

### Run Analyse
It does the same point again you had with base points or refinement. Due to the fact, that during modeling the mount refines, the model changes
each star. With that Dry run without changing the model you get a true difference between the model and the actual solved images.
So far I had only simulation data to test. I'm waiting for next good skies to check if all went good. If you would like to test it,
please feedback, what do you want to see. It should be no problem to implement it.

## Installation:
You need and actual installation of Python 3.5 and PyQt5 and it runs only under Windows. I use Windows10 64 bit. 

### Python
So we start with the installation of Python. Necessary ist python >= 3.5
You will find the download at:
<pre>https://www.python.org/downloads/</pre> 
The actual version is v 3.5.2. Please download it and install the package on your computer. Please remind to check the 'add to python path'
checkbox before starting the installation, otherwise you will not find the appropriate path set in you environment.

### MountWizzard
Just type 
<pre>pip install mountwizzard</pre>
to install the tool as package on your computer. You don't need to download the files from GitHub anymore, but if you still would like to test
further development versions, please feel free to do it. Just copy the files in a working directory and start the MountWizzard like you've done it before.

You can upgrade the MountWizzard by 
<pre>pip -install --upgrade --no-cache-dir mountwizzard</pre>
In most cases all dependencies were solved and installed as well.

### Running MountWizzard
You can run the MountWizzard from any working directory where you have write access to. You run the the MountWizzard out of the working 
directory with the command
<pre>pythonw.exe "c:\Users\XXX\AppData\Local\Programs\Python\Python35\Lib\site-packages\mountwizzard\mountwizzard.py</pre>
where XXX is you username. There might be some differences because of you windows installation. Just search for mountwizzard.py on your harddisk.
This seems a little bit strange to run, but I found so far no better way to use the distribution capabilities of python than 'baking' a package.


All necessary directories in the working directory will be created if not present. 
If you have some files already from earlier versions or separate working directories, just copy them to the adequate place. 

### ASCOM framework
If you didn't already install the ASCOM Framework on you computer for astronomy use, please do so now. 
You will find the download at:
<pre>http://ascom-standards.org</pre>
The actual version is 6.2. Please download it and install the package on your computer.

### ASCOM drivers
Please install Per Frejval 10micron ASCOM driver and if you have the Stickstation as well, please do so with Per Frejval ASCOM Stickstation driver, too. 
Another drive is used: OpenWeather ASCOM driver should be installed. For the first configuration you need an API key from OpenWeather. Please follow the instructions on http://openweathermap.org/api
how to get one.

## Usage:
Choose the settings you would like. Configuration of Ascom environment could be done via settings

## Logfiles or console output:
The message:
<pre>UserWarning: Could not find appropriate MS Visual C Runtime library or library is corrupt/misconfigured; 
cannot determine whether your file object was opened in append mode.  
Please consider using a file object opened in write mode instead. 
'Could not find appropriate MS Visual C Runtime '
 </pre>
 could be ignored. This is an issue from ctype python library, which is already known and doesn't influence functionality of mountwizzard.
see:
<pre> mscvrt not found when calling fits.open() on Python 3.5 on Win10 #4342
</pre>

### Remarks for professionals:
The mount_ui.ui file is the PyQt Designer file. If you would like to change designs or rearrangements, you could
customize your gui. Please note: this is a part for developers, which are familiar with python development.
you hae to generate the adequate python file for the gui with
<pre>pyuic5 mount_ui.ui -o mount_ui.py</pre>
in the same directory. If the commands are strange to you: don't touch the files :-).

### Finally
The use this software is at your own risk! No responsibility for damages to your mount or other equipment or your environment.
Please take care yourself !

Hope this makes fun and help, CS Michel
