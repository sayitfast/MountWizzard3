## Setting / config of UTC Data / MPC / TLE

<img src="pics/settings_uploads.png"/>

### Area 1: Webservice for space data

Most of the data will be downloaded from the minor planet center:
<pre>
http://www.minorplanetcenter.net/iau/MPCORB
</pre>

MountWizzard download data from the following sites:
<pre>
    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMETS = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    ASTEROIDS_MPC5000 = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    ASTEROIDS_NEA = 'http://www.minorplanetcenter.net/iau/MPCORB/NEA.txt'
    ASTEROIDS_PHA = 'http://www.minorplanetcenter.net/iau/MPCORB/PHA.txt'
    ASTEROIDS_TNO = 'http://www.minorplanetcenter.net/iau/MPCORB/Distant.txt'
    SPACESTATIONS = 'http://www.celestrak.com/NORAD/elements/stations.txt'
    SATBRIGHTEST = 'http://www.celestrak.com/NORAD/elements/visual.txt'
</pre>

You need a internet connection for doing this. You can download only a portion of the data or just download all files. The files
are stored in your
<pre>/config</pre>
directory inside your working directory.

### Area 2: Mount upload.

Actually there is no interface or API offered from 10micron to upload data by an external program. Therefore MountWizzard tries to
automate the original 10mircon updater software and does the job for you. I hope this hold for longer times as changes in workflow or
any other changes in the updater software will break this feature. We'll see.

Anyway: if you downloaded a data file, the checkbox for uploading it will be set automatically. There are some constraints in the
feature setup. The mount computer only allows one set of satellite data. So checking SpaceStation and Brightest Satellites will lead
in uploading Brightest Satellites only. There is no function right now to merge the databases. Please choose the one you would like
to have.

The mount computer has to memories for comets and asteroids data, so you can update them both. Because there is a lot of data in and
juggling around with the handbox to find the right entry for starting comet tracking, I added a quick filter feature for comets and
asteroids: If you check Filter MPC Files, MountWizzard takes the downloaded files and only upload that part of the entries, where the
filter expression is found. You can have multiple expressions, but you have to comma seperate them. It looks just for the string in the
file, not the comet or asteroid name !

[Back to configuration](configuration.md)

[Back to Home](home.md)