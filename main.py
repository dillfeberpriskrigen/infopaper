#!/usr/bin/python3

import os
import re
import subprocess
from icalendar import Calendar, Event
import datetime
import time
import json
from zoneinfo import ZoneInfo

pwd = os.path.dirname(__file__)+'/'

from functions import decode, dimensions,checkupdate, text, longest_text, cal_coordinates, wttr
from schemaprint import schemaprint
from colors import colors
with open("config.json", "r", encoding="utf-8") as f:
    Config = json.load(f)


wallpaper = pwd+Config["files"]["infile_path"]


def main():
    print("Main method call")
if __name__ =='__main__':
    main()
print("Sleeping a few seconds to establish internet connection.") # Tror jag behöver ett mindre hackigt sätt att lösa det här
#for i in range(1,4):
#    time.sleep(3)
#    print(i*5, " seconds slept")
print("Starting update...")
rb = subprocess.check_output([pwd+'/scripts/rebootcheck.sh'], shell = True)
rebootcheck = re.sub(r"b",'',str(rb), count=1)
rebootcheck = re.sub(r"['\\n]",'',str(rebootcheck))
day = subprocess.check_output(["date", '+"%d"'])
day = decode(day)
weekday = subprocess.check_output(["date", '+"%A vecka %V"'])
weekday = decode(weekday)
date = subprocess.check_output(["date", '+"%d/%m/%y"'])
date = decode(date)
#Första funktionen kallas med bakgrunden, sedan tar default över

w,h = dimensions()
xmid = w/2
xmidhalf = w/4
xcorner = w/16
ymid = h/2
ymidhalf = h/4
ycorner = h/15
textheight=65

textlist = [date,weekday,checkupdate()]
rightalign,heightalign=longest_text(textlist,Config["files"]["fontsize_big"])

text(date,w-xmidhalf-65,h-ymidhalf,colors[1],Config["files"]["font"],Config["files"]["fontsize_big"],rightalign,0, wallpaper)
text(weekday, w-xmidhalf-65, h+65-ymidhalf,colors[3],Config["files"]["font"],Config["files"]["fontsize_big"], rightalign)

text(checkupdate(),w-xmidhalf-65,h+textheight*2-ymidhalf,colors[2],Config["files"]["font"],Config["files"]["fontsize_big"],rightalign)

wttr_list = wttr(Config["wttr"])
for i in range(len(wttr_list)):
    text(wttr_list[i],w-xmidhalf-65,100+40*i,colors[1],Config["files"]["font"],Config["files"]["fontsize_small"],rightalign)

if rebootcheck != "No reboot required.":
    text("Reboot required", xcorner,h-ycorner, colors[2],Config["files"]["font"],Config["files"]["fontsize_small"])

cal_coordinates(xcorner,h-ymidhalf)
#schemalist = schemaprint() # Har inte haft ett schema där på år
#for i in range(len(schemalist)):
#    text(schemalist[i], xcorner,ymidhalf+40*i,colors[1],20,0,0)
## End of program update wallpaper ##
subprocess.run([Config["files"]["background_setter"],Config["files"]["setter_args"],pwd+"/resources/infopaper.png" ]) #Look into how backgrounds are set again. This is a security risk.
