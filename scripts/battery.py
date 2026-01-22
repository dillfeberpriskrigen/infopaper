#!/usr/bin/env python3

path = "/sys/class/power_supply/"
with open ( "/sys/class/power_supply/BAT0/capacity") as f:
    for line in f:
        a= float(line)
with open ( "/sys/class/power_supply/BAT1/capacity") as f:
    for line in f:
        b= float(line)
with open ( "/sys/class/power_supply/AC/online") as f:
    for line in f:
        state= int(line)
bat=a/2+b/2
#Jag vill skapa en funktion som tar in BATx status, energy_now energy_full 
def battery():
    pass 

#status =path+/BAT0/status
##**kwargs är wildcard för en okänd mängd keywords, jag tänker att om man tar en ls av katalogen */power_supply 
#Så borde det rimligtvis gå att få typ mängden ls -1 som kör då typ 0..1 för BAT 
def charging(state):
    if state:
        return "charging"
    else:
        return "discharging"
def status(capacity, state):
    if capacity >= 51:
        if capacity >= 76:
            return "[####]:", state
        if capacity <= 75:
            return "[### ]:", state
    if capacity <= 50:
        if capacity >= 26:
            return "[##  ]:", state
        if capacity >= 11 and capacity < 25:
            return "[#   ]:", state
        else:
            return "[    ]:", state

#def dunst_notification(state):
#    subprocess.Prun(["dunstify","hej" ])


print(status(bat,charging(state)))

