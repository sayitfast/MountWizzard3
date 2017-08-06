## Managing Mount Models

<img src="pics/tab_managemountmodel.png"/>

Managing mount models is an advanced part of working with MountWizzard and you setup. If you don't have a need for that, it's fine.
But let's explain what you could do.

First of all you should be aware that with MountWizzard you are using two computers (mount computer) and the one where MountWizzard
is installed to manage your pointing models. the design of the 10micron mount computer is done in a way to be able to to all things
without an additional computer, just by using the handcontroller attached to the mount. This means that actually all computation of
models only takes place inside the mount computer. From the outside world you only could feed the data, all other things happen inside
the mount computer. Internal states, data and many more information in not accessible from outside. And the data internally stored is
the data which is needed for the model. So all information you have from the model making process (temperatures, points, config of
setup and especially all images and camera topics, results from plate solver) are lost after you made a model.

MountWizzard keeps all this data and stores it in a second set of model data outside the mount. Done this you have access to all data
to recap events, you would like to take care of to optimise you gear or setup. MountWizzard tries to keep these two data set of one
pointing model synced like "twins". If everything works out fine, not problem, if errors happen in the mount or MountWizzard or you
interfere by doing manual steps at the same time with the handcontroller for example, things might get mixed up. Not a big deal,
because you still have your pointing model in the mount - so imaging can talk off. The part you will miss is the extended analyse and
tweaking capabilities. You recover automatically with the next successful model making run.

### Area 1 - Optimise actual model

In this area you could check the data of the actual used pointing model data. Once pressed "show actual model", the mount computer
data will be downloaded and you get the list of model stars, their location in hemisphere and error values.

<b>delete worst point</b> allows you to remove the point with the largest error from the list of model stars. This makes the mount
computer recalculating the pointing model and normally results in a better overall model, if that removed point was an outlayer. After
that, the actual model will by downloaded again and the list of stars (now on star less) will be shown.

<b>run optimise</b>: if you are lazy, MountWizzard could do the job for you automatically. You could set a target value of overall
error (RMS) for your model (yellow part) removing of the worst point will be done as long as the actual error is higher than the desired
one. In case the desired model error could not be reached, the mount computer will have removed (or emptied) your complete model.
But do not hesitate to use this function: before starting the optimisation, the actual model will be saved as "BACKUP"
(see area 3 section). If the optimisation fail, just load the "BACKUP" and start over.

I would recommend to lower the target RMS step by step and see, how much stars will be removed to get to the next level. Over time
you get a good feeling how the numbers could be.

There is an alternatively way of presenting the list of modeling stars and the errors: [the polar plot](firststeps41.md). If you
check the checkbox "polar plot" you will get instead of the list of star a polar plot.

### Area 2 - actual model status

This information is basically all the information the mount computer can give you how to setup you mount right. It's exactly
the information you get via the handcontroller in the menu "align info". Available from mount firmware 2.15.1 onwards.

### Area 3

As already mentioned, MountWizzard saves model data on your computer as well the pointing model under a certain name in the mount
computer. The models in the mount computer and on your computer filesystem have the same name. Files are stored on your computer in
the directory
<pre>/analysedata</pre>
You have the possibility to maintain several models e.g. for DSO tracks. There is no difference in the amount of data between the
models, but take care that the first 3 ones are used from MountWizzard to optimise usability.

The BACKUP model is used for automatic backup e.g. for optimisation runs.

The BASE model is saved automatically after a base model run and reloaded - if existent - before a refinement run.

The REFINE model is save automatically after a refinement run is finished.

[Back to first steps](firststeps.md)

[Back to Home](home.md)