#!/usr/bin/python3

#########################################
#Script Name:				#
#Decription: 				#
#Args:					#
#Author:				#
#Email:					#
#########################################

from PIL import Image, ImageDraw, ImageFont
import io
import sys
import json
import requests
import numpy as np #Jag borde börja kommentera vad jag använder olika libs till.. Jag kanske använder numpy för transponering? 
# Define the URL to fetch data from
def wttr(city ="Linköping"):
    url = "http://wttr.in/"
    flags = "?format=j1"
    url = url+city+flags

    result = requests.get(url)

    jsonny = result.json()
    jsonny["current_condition"][0]["FeelsLikeC"]

    jsonny["weather"][0]["hourly"][3] #Första indexet visar vilken dag rapporten är för. 0 idag, 1 i morgon 2 i övermorgon. Det andra indexet är vilket tretimmarsintervall som gäller.
    Propertylist = ["time","tempC", "FeelsLikeC","chanceofrain","precipMM","humidity","windspeedKmph" ]
    jsonny["weather"][0]["hourly"][6]
    result = [["Desc         ",
               "Time         ",
               "Temp         ",
               "Feels like   ",
               "% rain       ",
               "Precipitation",
               "Humidity     ",
               "Windspeed    "]]
    for hour in range(3,7):
        proppie = [jsonny["weather"][0]["hourly"][hour]["weatherDesc"][0]["value"]] + [jsonny["weather"][0]["hourly"][hour][prop] for prop in Propertylist]
        result.append(proppie)

    transpose = np.array(result).T.tolist()
    transpose[1] = ["Time", "09:00", "12:00", "15:00", "18:00"]

    lsty = []#Temporär
    for i in range(1,len(transpose[0])):
        temp = transpose[0][i]+" at "+transpose[1][i] +". Temp:"+ transpose[2][i] + " Feels like:" + transpose[3][i] +". %-rain:"+ transpose[4][i] + " rain:" + transpose[5][i]
        lsty.append(temp)
    return lsty
    
lsty = wttr()
for i in lsty:
        print(i)
