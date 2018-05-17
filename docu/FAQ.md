## <img src="pics/mw.png" width='64' height='64'/>What to do if ?

### Error Messages and what to do ?

#### - Finishing application on Mac and Linux
If you are closing MountWizzard3 on Mac or Linux, you will see in the terminal:
<pre>QCoreApplication::postEvent: Unexpected null receiver</pre>
This is an bug of actual Qt5.10.1 implementation, but has no effect, because you are anyway
closing the app.
