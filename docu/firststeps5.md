## Model Analyse TAB

<img src="pics/tab_modelanalyse.png"/>

As expert mode, MountWizzard allows special slewing and analyses use case to test your setup and give some hint about
possible improvements to make. Some of them are experimental and it is open, to which extend you can use the data. There
is no "real" and "defined" interpretation of the results available, but I would like to giv some hints and I'm open to
add remarks and comments to the documentation.

### Area 1 - Analyse Time Flexure

Time flexure is a topic where your setup changes over time. Obvious cooling down is needed before starting imaging, but also
mechanics in your rig might subject to change over time. <b>"Analyse time flexure"</b> allows you to slew to the given position
an taking the given number of cycles picture, plate solve it and log the error over time. The time steps could be given in
the "delay" setting.

MountWizzard stores the data on your computer and you can review it by selecting it and showing the data in the Analyse Window
(see area 4)

### Area 2 - Analyse Hysterese

Like time flexure, MountWizzard allows you to slew between two given points (there might be some extensions to that feature) and
measure the deviations with respect to the movement done between these positions. The first point is the reference, where imaging
and plate solving takes place, the second is the hysterese point, which defines the movement.

### Area 3 - Cancel Analyse Run

Like in model building, your can stop any analyse run just by pressing this button. Please wait, until the button returns from
red to default, because the running cycle will be finished.

### Area 4 - Analyse data selection

All analyse data will be stored in your working directory in the subfolder
<pre>/analysedata</pre>
and could be reviewed any time later. Once MountWizzard does an analyse run or even a base model or refinement model run, the
last filename will be set automatically. If you press "open analyse window", it will be shown -or- if the window is already open
data will be updated. Examples and working with analyse data will be explained the [section analyse data](analysedata.md)

### Area 5 - Batch model making

Normally model making is a continuous flow of slewing, finding position (manually or with imaging and plate solving), telling the
mount the right position, the mount computer will calculated the errors and adapting the internal pointing model and you move on
with the next point. This flow is also automated with MountWizzard. You have seen the explanations in
[Make Mount Model](firststeps3.md).

Since firmware 2.8.15 the 10micron mount computer offers the function to calculate a model based on pure data. This means you
are using just the calculation algorithm inside the mount without image taking and slewing the telescope, but you need the data
for the algorithm. The data needed is quite simple: time (sidereal), the pointing information of the mount (ra, dec), the pierside
of the mount (in case you have points which could be accessed from both sides) and of course the pointing information which is
the truth in this moment. Whit this data, the mount computer can calculate the deviations and build a pointing model.

Now, where to get this data from ? Simple answer: MountWizzard stores this data in every base / refinement / combined / etc. model
or analyse run on your computer. Example: If you made a combined base / refinement model run, you have all the points with it's
data to build a new model in a "batch" run. Just feeding the data again. The mount computer will calculate the new model and
replace the actual one after finishing the calculation.

This function could also be used for restoring a model in the mount computer, when you lost this data in the mount for whatever
reason. Just pick the data, which was stored after you model run you would like to recover, and do a batch run with this data.
The result is new model, but based on the same data. It might not be identically, but very close.

[Back to first steps](firststeps.md)

[Back to Home](home.md)