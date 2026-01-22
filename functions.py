#!/usr/bin/python3
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import os
import datetime
import calendar
from colors import colors
import io
import sys
import json
import requests
import numpy as np
pwd = os.path.dirname(__file__)+'/' # Config
wallpaper = pwd+'/resources/background.png' # Config 
infoPaperPath = pwd+'resources/infopaper.png'

def decode(var):
    var = var.decode('utf-8')  # Config
    var = var.replace('"', '')
    return var

def dimensions(wallpaper = wallpaper): 
    image = Image.open(wallpaper)
    w,h = image.size
    return w,h


def checkupdate() -> str: 

    updatelist = None
    try:
        updatelist = subprocess.check_output(["checkupdates"]) #Arch dependant
        updatelist= decode(updatelist)
        updatelist = updatelist.split('\n')

        updates = 0
        for i in updatelist:
            updates += 1
        return str("Uppdateringar: "+str(updates))
    except subprocess.CalledProcessError as a: #Det här hanterar om inga uppdateringar finns. Checkupdates returnerar $? felstatus 2 vilket subprocess tolkar som ett fel. Det här borde skriva ut ingenting.
        output = a.output
        return "" #Måste returnera str


def text(text,x,y, color,font, fontsize=65, rightalign=0, heightalign=0,wallpaper = infoPaperPath) -> None : #Outputfilen borde definieras i en config fil
    w,h = dimensions()
    if rightalign != 0:
        x = w -rightalign-(x-w)
    #y = y + heightalign
    image =  Image.open(wallpaper)
    print(font)
    print(type(font))
    font = ImageFont.truetype('DejaVuSans-Bold.ttf',fontsize) # Font borde definieras i en config
    draw = ImageDraw.Draw(image)
    x_mod, y_mod = draw.textbbox((0,0),text,font)[2:] #Returnerar bredd och höjd av textobjektet 
    if x + x_mod > w: #Gör så att texten inte skrivs utanför bilden
        print("x: ",x,"w: ",w,"bound: ",x_mod,"x+bound: ",x+x_mod)
        x = w-x_mod-65
        #print(x)
    if y + y_mod > h:
        y -= y_mod
# Behöver skapa en draw funktion
    draw.text((x,y), str(text), font=font, fill=(color))
    image.save(infoPaperPath) #Config




def longest_text(textlist, fontsize) -> int :
    wallpaper = infoPaperPath #Config
    #font = ImageFont.truetype('/usr/share/fonts/TTF/OpenSans-Bold.ttf',fontsize)
    font = ImageFont.truetype('DejaVuSans-Bold.ttf',fontsize) # Config
    image =  Image.open(wallpaper)
    draw = ImageDraw.Draw(image)
    largest_x = 0
    largest_y = 0
    for i in textlist:
        x_mod, y_mod = draw.textbbox((0,0),i,font)[2:] #Returnerar bredd och höjd av textobjektet
        if x_mod >= largest_x:
            largest_x = x_mod
        if y_mod >= largest_y:
            largest_y = y_mod
    return largest_x,largest_y

def cal_coordinates(posx = 200,posy = 200, fontsize = 20, color = colors[2]) -> None :
    today = datetime.date.today()
#debugtest    today = datetime.date(2022, 4, 18)
    day = today.strftime("%d")
    fontwidth = fontsize*1.83 #Borde kunna justeras genom att ta en teckenkombination som är typ, den bredaste typ "  " och hämta draw.textbbox för att få den faktiska fontbredden och höjden. ## FRAMTIDA FILIP HÄR: Ja absolut, det enda jag behöver göra är att räkna antalet tecken och sedan ta mellanslagsbredden och multiplicera med antalet tecken. Det här skulle kunna göras separat så att det enbart behöver göras på uppstart... Fast, eller nej. Det måste göras per antalet fonts. Så jag behöver ha en font-lista och generera en font-bredd dict. 
    fontheight =  fontsize*1.15 # Det funkar, borde funka bättre.
    if day[0] == '0':
        day = day.lstrip('0')

    year = today.strftime("%Y")
    month = today.strftime("%m")
    ascii_calendar = calendar.month(int(year),int(month))
    cal = [date.split() for date in ascii_calendar.strip().split("\n")]
    week = {'Mon': 1,'Tue': 2,'Wed': 3,'Thu': 4,'Fri': 5,'Sat': 6,'Sun': 7} #Kanske är onödig nu. Ska vi inte testa att ta bort den då?
    weeknum = 0
    day = int(day)
    # Add offset based on the first day of this month
    day += datetime.date(today.year, today.month, 1).weekday()-1
    if day > 7:
        weeknum = int(int(day)/7)
    else:
        weeknum = 0 #Ändrade från 1 till 0 när den första hamnade på en rad för långt ner. Den här kanske är överflödig nu 
    weeknum = weeknum +2
    box_embiggener = 2 #3
    weekday_number = int(week.get(today.strftime("%a")))
    weekday_number = weekday_number -1

    image =  Image.open(infoPaperPath) #Config
    draw = ImageDraw.Draw(image)
    x_marker = posx+(fontwidth*weekday_number)
    y_marker = posy+fontheight*weeknum

    shape = [(x_marker-box_embiggener,y_marker-box_embiggener),(x_marker+fontsize+box_embiggener,y_marker+fontsize+box_embiggener)] #Storleken av markören borde vara storleken av ett tecken

    font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSansMono.ttf',fontsize) #Config
    draw.rounded_rectangle((shape))
    draw.text((posx,posy), str(ascii_calendar), font=font, fill=(colors[2])) 
    image.save(infoPaperPath) # Config

def wttr(config: dict):
    """
    Get weather forecast for a city using wttr.in, fully configurable via a dictionary.
    Default is wttr in the config.json.

    config keys:
        city: str - city name
        hours: list[int] - hourly indexes to include
        properties: list[str] - weather properties to extract
        transpose_times: list[str] - labels for the hours (for display)
    """
    city = config.get("city", "Linköping")
    hours = config.get("hours", [3, 4, 5, 6])
    Propertylist = config.get("properties", ["time","tempC","FeelsLikeC","chanceofrain","precipMM","humidity","windspeedKmph"])
    transpose_times = config.get("transpose_times", ["09:00", "12:00", "15:00", "18:00"])

    url = f"http://wttr.in/{city}?format=j1"
    print(url)
    response = requests.get(url)
    jsonny = response.json()

    result = [["Desc", "Time", "Temp", "Feels like", "% rain", "Precipitation", "Humidity", "Windspeed"]]

    for hour in hours:
        proppie = [jsonny["weather"][0]["hourly"][hour]["weatherDesc"][0]["value"]] + \
                  [jsonny["weather"][0]["hourly"][hour][prop] for prop in Propertylist]
        result.append(proppie)

    transpose = np.array(result).T.tolist()
    transpose[1] = ["Time"] + transpose_times  # replace time row with readable times

    lsty = []
    for i in range(1, len(transpose[0])):
        temp = f"{transpose[0][i]} at {transpose[1][i]}. Temp: {transpose[2][i]} Feels like: {transpose[3][i]}. %-rain: {transpose[4][i]} rain: {transpose[5][i]}"
        lsty.append(temp)

    return lsty

