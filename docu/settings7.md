## Remote access

<img src="pics/tab_settings_ascommountdriver.png"/>

### Area 5: Remote Access for MW.

A first shot enabling backyard automation. When checked, MountWizzard will listen on port 3495 for commands send over via TCP. Actually
the only command is
<pre>shutdown</pre>
You could send the command on a windows pc by tool, which allows you to send a string via TCP. Here an example: Google for "NCAT Portable"
and download that tool. You can move the exe file in a directory which is available from your scripting environment (SGPro etc.) The command
for shutting down MountWizzard woudl be from the command line (or batch file):

<pre>echo shutdown | ncat --send-only localhost 3495</pre>

Still experimental, you might run into troubles. I let you know, when it works!

[Back to settings](settings.md)

[Back to first steps](firststeps.md)

[Back to Home](home.md)