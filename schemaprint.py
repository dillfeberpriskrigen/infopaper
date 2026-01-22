from icalendar import Calendar, Event
import datetime
from zoneinfo import ZoneInfo


import os


pwd = os.path.abspath(__file__)
pwd = pwd[:-14] #Temporär lösning för att ta bort filnamnet från strängen
# Tror den här temporära lösningen varit temporär i fyra år nu. :D
wallpaper = pwd+'/resources/background.png'





def schemaprint() -> list:
    def schemaloop(schema, day) -> list:
        return_list = []
        for component in schema.walk():
            if component.name == "VEVENT": #Den här behöver finnas så att vi inte parsear tomma entries
                dtstart = component.get('dtstart').dt
                start_gmt = dtstart + datetime.timedelta(hours=timezone) # OBS väldigt hackig lösning
                dtend = component.get('dtend').dt
                end_gmt = dtend + datetime.timedelta(hours=timezone)

                #Funkar inte local_dtstart = dtstart.replace(tzinfo=local_timezone)
                if dtstart.strftime("%D") == day.strftime("%D"):
                    description = str(component.get('description'))
                    description = description.split('\n')

                    return_list.append(str("Tid: "+ start_gmt.strftime("%H:%M")+ " till "+  end_gmt.strftime("%H:%M ")+component.get('location')))
                    return_list.append(" || ".join(description[:3])) 
        return return_list
    local_timezone=ZoneInfo("Europe/Stockholm") #Behöver göras dynamiskt
    cal = Calendar()
    DST = False #Här måste justering för vintertid och sommartid automatiseras sommartid är 2 medan vintertid är 1
    if DST == True:
        timezone = 2
    else:
        timezone = 1
    #today = datetime.datetime.today() + datetime.timedelta(days=2) #Bara för debug
    today = datetime.datetime.today() 
    tomorrow = today + datetime.timedelta(days=1)
    g = open(pwd+'schema.ics','rb') # Borde automatiseras. Jag tror inte att det här går att automatiseras. Kanske om man hämtar alla scheman på samma gång i samma ICS fil? Eller skapar någonting där jag bara kan ta nya ics filer och lägga till dem till schema.ics
    gcal = Calendar.from_ical(g.read())
    return_list = []
    temp = schemaloop(gcal,today)
    slackercount = 0
    if temp == []:
        return_list.append("--- Dagens Schema ---")
        return_list.append("Inget idag! :D")
        slackercount += 1
    else:
        return_list.append("--- Dagens Schema ---")
        return_list.extend(temp)

    temp = schemaloop(gcal,tomorrow) #Kör funktionen en gång och sparar i minne så jag slipper köra den flera gånger. 
    if temp == []:
        return_list.append("--- Morgondagens Schema ---")
        return_list.append("Inget i morgon! :D")
        slackercount += 1
    else:
        return_list.append("--- Morgondagens Schema ---")
        return_list.extend(schemaloop(gcal,tomorrow))

    if slackercount == 2:
        return_list.append("Amen va tomt det är, går man filfack eller!")
    g.close()
    return return_list
