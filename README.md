A collection of scripts that takes some standard data and prints it onto a picture and sets it as background.

If you want to be able to use it the way I have then it has been working well for the past four years. But it is more a proof of concept than finished working software. It is very inefficient but as it only runs (for me) once per day the inefficiency is immaterial.

The current functionality supports:

Taking in any image as the wallpaper foundation.
Printing ics files for today and tomorrow. 
Fetching weather at wttr predefined intervals.
Testing to see if the kernel has updated.
Showing current date in a calendar (based on the linux cal command).
The text function can print pretty much anything. I was thinking about doing daily poems or qoutes.

Things that are hardcoded:

There are some fontadjustments that will always (i think) need to be done manually. These are currently hardcoded. It did not make much sense to write any other implementation before functional gui.

Placements. For above reason.

Safety issues:

This launches scripts outside of python, this is not safe at all.  