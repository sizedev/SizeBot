import discord
from discord.ext import commands
import re
import datetime
import sys
import os
import time
from datetime import date
from datetime import *
import math
import random
from decimal import *
from colored import fore, back, style, fg, bg, attr
from pathlib import Path
import string
import traceback
from discord.ext import commands
from math import *
import asyncio
import codecs

#TODO: Make this do something useful.
class DigiException(Exception):
    pass

#Version.
version = "2.0.1"

#Defaults
defaultheight = Decimal(1617500) #micrometers
defaultweight = Decimal(69472900) #milligrams
defaultdensity = Decimal(1.0)

#Constants
newline = "\n"
monikalines = ["What? I don't know anyone named Monika.",
"I don't know anyone named Monika! hehheh...",
"Hey wha-- er...", "Did someone say my n- um... Monika? Weird.",
"I hear Monika was the best character in Doki Doki. I may be a bit biased though 'cause... never mind.",
"Monika? :sweat_smile: Never heard of her."]
folder = ".."
noboru = 291654189833256960
sizebot_id = 344590087679639556
digiid = 271803699095928832

#Array item names.
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7

#Statsplus array item names.
FOOT = 0
BUST = 1
PNIS = 2

#Monika line gen.
def monikaline():
    return random.choice(monikalines)

def regenhexcode():
    #16-char hex string gen for unregister.
    hexdigits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "a", "b", "c", "d", "e", "f"]
    lst = [random.choice(hexdigits) for n in range(16)]
    hexstring = "".join(lst)
    hexfile = open("hexstring.txt", "r+")
    hexfile.write(hexstring)
    hexfile.close()

def readhexcode():
    #Read the hexcode from the file.
    hexfile = open("hexstring.txt", "r+")
    hexcode = hexfile.readlines()
    hexfile.close()
    return str(hexcode[0])

#ASCII art.
ascii = """
. _____ _        ______       _   _____ .
./  ___(_)       | ___ \     | | |____ |.
.\ `--. _ _______| |_/ / ___ | |_    / /.
. `--. \ |_  / _ \ ___ \/ _ \| __|   \ \.
./\__/ / |/ /  __/ |_/ / (_) | |_.___/ /.
.\____/|_/___\___\____/ \___/ \__\____/ .
                                         """

#Configure decimal module.
getcontext()
context = Context(prec=225, rounding=ROUND_HALF_EVEN, Emin=-9999999999, Emax=9999999999,
        capitals=1, clamp=0, flags=[], traps=[Overflow, DivisionByZero,
        InvalidOperation])
setcontext(context)

#Get number from string.
def getnum(string):
    numberarray = [str(s) for s in re.findall(r'\d+\.?\d*', string)]
    return Decimal(numberarray[0])

#Get letters from string.
def getlet(string):
    letterarray = [str(s) for s in re.findall(r'[a-zA-Z]+', string)]
    return letterarray[0]

#Remove decimals.
def removedecimals(output):
    if ".00" in output:
        output = output.replace(".00", "")
    elif ".10" in output:
        output = output.replace(".10", ".1")
    elif ".20" in output:
        output = output.replace(".20", ".2")
    elif ".30" in output:
        output = output.replace(".30", ".3")
    elif ".40" in output:
        output = output.replace(".40", ".4")
    elif ".50" in output:
        output = output.replace(".50", ".5")
    elif ".60" in output:
        output = output.replace(".60", ".6")
    elif ".70" in output:
        output = output.replace(".70", ".7")
    elif ".80" in output:
        output = output.replace(".80", ".8")
    elif ".90" in output:
        output = output.replace(".90", ".9")
    return output

def round_nearest_half(number):
    return round(number * 2) / 2

def place_value(number):
    return ("{:,}".format(number))

async def nickupdate(ctx, userarray):
    if userarray[CHEI] == "None":
        userarray[CHEI] = userarray[BHEI]
        await ctx.send("<@{0}>: Error in size value: Size value returned 'None'. Resetting to base height.").format(message.author.id)
    if ctx.message.author.id != 291654189833256960:
        if userarray[UNIT] == "M\n":
            if userarray[SPEC] == "None\n":
                nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + "]"
                if len(nick) > 32:
                    nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSV(userarray[CHEI]) + "]"
                    if len(nick) > 32:
                        nick = userarray[NICK] + " [8]"
                await ctx.message.author.edit(nick = nick)
            else:
                nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + ", " + userarray[SPEC] + "]"
                if len(nick) > 32:
                    nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + "]"
                    if len(nick) > 32:
                        nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSV(userarray[CHEI]) + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK] + " [8]"
                await ctx.message.author.edit(nick = nick)
        else:
            if userarray[SPEC] == "None\n":
                nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + "]"
                if len(nick) > 32:
                    nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSVUSA(userarray[CHEI]) + "]"
                    if len(nick) > 32:
                        nick = userarray[NICK] + " [8]"
                await ctx.message.author.edit(nick = nick)
            else:
                nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + ", " + userarray[SPEC] + "]"
                if len(nick) > 32:
                    nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + "]"
                    if len(nick) > 32:
                        nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSVUSA(userarray[CHEI]) + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK] + " [8]"
                await ctx.message.author.edit(nick = nick)

#Read in specific user.
def read_user(user_id):
    user_id = str(user_id)
    with open(folder + "/users/" + user_id + ".txt") as f:
        #Make array of lines from file.
        content = f.readlines()
        #Replace None.
        if content[BWEI] == "None" + newline:
            content[BWEI] = str(defaultweight) + newline
        if content[BHEI] == "None" + newline:
            content[BHEI] = str(defaultweight) + newline
        if content[CHEI] == "None" + newline:
            content[CHEI] = content[3]
        #Round all values to 18 decimal places.
        content[CHEI] = str(round(float(content[CHEI]), 18))
        content[BHEI] = str(round(float(content[BHEI]), 18))
        content[BWEI] = str(round(float(content[BWEI]), 18))
        return content

def read_userline(user_id, line):
    content = read_user(user_id)
    return content[line - 1]

#Write to specific user.
def write_user(user_id, content):
    user_id = str(user_id)
    #Replace None.
    if content[BWEI] == "None" + newline:
        content[BWEI] = str(defaultweight) + newline
    if content[BHEI] == "None" + newline:
        content[BHEI] = str(defaultweight) + newline
    if content[CHEI] == "None" + newline:
        content[CHEI] = content[3]
    #Round all values to 18 decimal places.
    content[CHEI] = str(round(float(content[CHEI]), 18))
    content[BHEI] = str(round(float(content[BHEI]), 18))
    content[BWEI] = str(round(float(content[BWEI]), 18))
    #Add new line characters to entries that don't have them.
    for idx, item in enumerate(content):
        if not content[idx].endswith("\n"):
            content[idx] = content[idx] + "\n"
    #Delete userfile.
    os.remove(folder + "/users/" + user_id + ".txt")
    #Make a new userfile.
    userfile = open(folder + "/users/" + user_id + ".txt", "w+")
    #Write content to lines.
    userfile.writelines(content)

#Read in specific user's plusstats.
def read_user_plus(user_id):
    user_id = str(user_id)
    with open(folder + "/plus/" + user_id + ".txt") as f:
        #Make array of lines from file.
        content = f.readlines()
        return content

#Write to specific user.
def write_user_plus(user_id, content):
    user_id = str(user_id)
    #Add new line characters to entries that don't have them.
    for idx, item in enumerate(content):
        if not content[idx].endswith("\n"):
            content[idx] = content[idx] + "\n"
    #Delete plusfile.
    os.remove(folder + "/plus/" + user_id + ".txt")
    #Make a new plusfile.
    userfile = open(folder + "/plus/" + user_id + ".txt", "w+")
    #Write content to lines.
    userfile.writelines(content)

#Count users.
members = 0
path = folder + '/users'
listing = os.listdir(path)
for infile in listing:
    if infile.endswith(".txt"):
        members += 1
print("Loaded {0} users.".format(members))

#Color styling for terminal messages.
def warn(message):
    return (fore.YELLOW + message + style.RESET)
def crit(message):
    return (back.RED + style.BOLD + message + style.RESET)
def test(message):
    return (fore.BLUE + message + style.RESET)

#Slow growth tasks.
tasks = {}

#Unit constants.
#Height [micrometers]
inch = Decimal(25400)
foot = inch * Decimal(12)
mile = foot * Decimal(5280)
ly = mile * Decimal(5879000000000)
au = Decimal(149597870700000000)
uni = Decimal(879848000000000000000000000000000)
infinity = Decimal(879848000000000000000000000000000000000000000000000000000000)
#Weight [milligrams]
ounce = Decimal(28350)
pound = ounce * Decimal(16)
uston = pound * Decimal(2000)
earth = Decimal(5972198600000000000000000000000)
sun = Decimal(1988435000000000000000000000000000000)
milkyway = Decimal(95000000000000000000000000000000000000000000000)
uniw = Decimal(3400000000000000000000000000000000000000000000000000000000000)

#Convert any supported height to 'size value', or micrometers.
def toSV(value, unit):
    unit = unit.lower()
    if (unit == "yoctometers" or unit == "yoctometer"):
        output = Decimal(value) / Decimal(10**18)
    elif (unit == "zeptometers" or unit == "zeptometer"):
        output = Decimal(value) / Decimal(10**15)
    elif (unit == "attometers" or unit == "attometer" or unit == "am"):
        output = Decimal(value) / Decimal(10**12)
    elif (unit == "femtometers" or unit == "femtometer" or unit == "fm"):
        output = Decimal(value) / Decimal(10**9)
    elif (unit == "picometers" or unit == "picometer"):
        output = Decimal(value) / Decimal(10**6)
    elif (unit == "nanometers" or unit == "nanometer" or unit == "nm"):
        output = Decimal(value) / Decimal(10**3)
    elif (unit == "micrometers" or unit == "micrometer" or unit == "um"):
        output = Decimal(value)
    elif (unit == "millimeters" or unit == "millimeter" or unit == "mm"):
        output = Decimal(value) * Decimal(10**3)
    elif (unit == "centimeters" or unit == "centimeter" or unit == "cm"):
        output = Decimal(value) * Decimal(10**4)
    elif (unit == "meters" or unit == "meter" or unit == "m"):
        output = Decimal(value) * Decimal(10**6)
    elif (unit == "kilometers" or unit == "kilometer" or unit == "km"):
        output = Decimal(value) * Decimal(10**9)
    elif (unit == "megameters" or unit == "megameter"):
        output = Decimal(value) * Decimal(10**12)
    elif (unit == "gigameters" or unit == "gigameter" or unit == "gm"):
        output = Decimal(value) * Decimal(10**15)
    elif (unit == "terameters" or unit == "terameter" or unit == "tm"):
        output = Decimal(value) * Decimal(10**18)
    elif (unit == "petameters" or unit == "petameter" or unit == "pm"):
        output = Decimal(value) * Decimal(10**21)
    elif (unit == "exameters" or unit == "exameter" or unit == "em"):
        output = Decimal(value) * Decimal(10**24)
    elif (unit == "zettameters" or unit == "zettameter" or unit == "zm"):
        output = Decimal(value) * Decimal(10**27)
    elif (unit == "yottameters" or unit == "yottameter" or unit == "ym"):
        output = Decimal(value) * Decimal(10**30)
    elif (unit == "inches" or unit == "inch" or unit == "in"):
        output = Decimal(value) * inch
    elif (unit == "feet" or unit == "foot" or unit == "ft"):
        output = Decimal(value) * foot
    elif (unit == "miles" or unit == "mile" or unit == "mi"):
        output = Decimal(value) * mile
    elif (unit == "lightyears" or unit == "lightyear" or unit == "ly"):
        output = Decimal(value) * ly
    elif (unit == "astronomical_units" or unit == "astronomical_unit" or unit == "au"):
        output = Decimal(value) * au
    elif (unit == "universes" or unit == "universe" or unit == "uni"):
        output = Decimal(value) * uni
    elif (unit == "kilouniverses" or unit == "kilouniverse" or unit == "kuni"):
        output = Decimal(value) * uni * Decimal(10**3)
    elif (unit == "megauniverses" or unit == "megauniverse" or unit == "muni"):
        output = Decimal(value) * uni * Decimal(10**6)
    elif (unit == "gigauniverses" or unit == "gigauniverse" or unit == "guni"):
        output = Decimal(value) * uni * Decimal(10**9)
    elif (unit == "terauniverses" or unit == "terauniverse" or unit == "tuni"):
        output = Decimal(value) * uni * Decimal(10**12)
    elif (unit == "petauniverses" or unit == "petauniverse" or unit == "puni"):
        output = Decimal(value) * uni * Decimal(10**15)
    elif (unit == "exauniverses" or unit == "exauniverse" or unit == "euni"):
        output = Decimal(value) * uni * Decimal(10**18)
    elif (unit == "zettauniverses" or unit == "zettauniverse" or unit == "zuni"):
        output = Decimal(value) * uni * Decimal(10**21)
    elif (unit == "yottauniverses" or unit == "yottauniverse" or unit == "yuni"):
        output = Decimal(value) * uni * Decimal(10**24)
    else:
        return None
    return output

#Convert 'size values' to a more readable format (metric).
def fromSV(value):
    value = float(value)
    output = ""
    if value <= 0:
        return "0"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), 2)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), 2)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), 2)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), 2)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), 2)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), 2)) + "nm"
    elif value < 10**3:
        output = str(round(Decimal(value), 2)) + "µm"
    elif value < 10**4:
        output = str(round(Decimal(value) / Decimal(10**3), 2)) + "mm"
    elif value < 10**6:
        output = str(round(Decimal(value) / Decimal(10**4), 2)) + "cm"
    elif value < 10**9:
        output = str(round(Decimal(value) / Decimal(10**6), 2)) + "m"
    elif value < 10**12:
        output = str(round(Decimal(value) / Decimal(10**9), 2)) + "km"
    elif value < 10**15:
        output = str(round(Decimal(value) / Decimal(10**12), 2)) + "Mm"
    elif value < 10**18:
        output = str(round(Decimal(value) / Decimal(10**15), 2)) + "Gm"
    elif value < 10**21:
        output = str(round(Decimal(value) / Decimal(10**18), 2)) + "Tm"
    elif value < 10**24:
        output = str(round(Decimal(value) / Decimal(10**21), 2)) + "Pm"
    elif value < 10**27:
        output = str(round(Decimal(value) / Decimal(10**24), 2)) + "Em"
    elif value < 10**30:
        output = str(round(Decimal(value) / Decimal(10**27), 2)) + "Zm"
    elif value < uni:
        output = str(round(Decimal(value) / Decimal(10**30), 2)) + "Ym"
    elif value < uni * (10**3):
        output = str(round(Decimal(value) / uni, 2)) + "uni"
    elif value < uni * (10**6):
        output = str(round(Decimal(value) / uni / Decimal(10**3), 2)) + "kuni"
    elif value < uni * (10**9):
        output = str(round(Decimal(value) / uni / Decimal(10**6), 2)) + "Muni"
    elif value < uni * (10**12):
        output = str(round(Decimal(value) / uni / Decimal(10**9), 2)) + "Guni"
    elif value < uni * (10**15):
        output = str(round(Decimal(value) / uni / Decimal(10**12), 2)) + "Tuni"
    elif value < uni * (10**18):
        output = str(round(Decimal(value) / uni / Decimal(10**15), 2)) + "Puni"
    elif value < uni * (10**21):
        output = str(round(Decimal(value) / uni / Decimal(10**18), 2)) + "Euni"
    elif value < uni * (10**24):
        output = str(round(Decimal(value) / uni / Decimal(10**21), 2)) + "Zuni"
    elif value < uni * (10**27):
        output = str(round(Decimal(value) / uni / Decimal(10**24), 2)) + "Yuni"
    else:
        return "∞"
    return removedecimals(output)

#Convert 'size values' to a more readable format (accurate).
def fromSVacc(value):
    value = float(value)
    output = ""
    if value <= 0:
        return "0"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), 3)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), 3)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), 3)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), 3)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), 3)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), 3)) + "nm"
    elif value < 10**3:
        output = str(round(Decimal(value), 3)) + "µm"
    elif value < 10**4:
        output = str(round(Decimal(value) / Decimal(10**3), 3)) + "mm"
    elif value < 10**6:
        output = str(round(Decimal(value) / Decimal(10**4), 3)) + "cm"
    elif value < 10**9:
        output = str(round(Decimal(value) / Decimal(10**6), 3)) + "m"
    elif value < 10**12:
        output = str(round(Decimal(value) / Decimal(10**9), 3)) + "km"
    elif value < 10**15:
        output = str(round(Decimal(value) / Decimal(10**12), 3)) + "Mm"
    elif value < 10**18:
        output = str(round(Decimal(value) / Decimal(10**15), 3)) + "Gm"
    elif value < 10**21:
        output = str(round(Decimal(value) / Decimal(10**18), 3)) + "Tm"
    elif value < 10**24:
        output = str(round(Decimal(value) / Decimal(10**21), 3)) + "Pm"
    elif value < 10**27:
        output = str(round(Decimal(value) / Decimal(10**24), 3)) + "Em"
    elif value < 10**30:
        output = str(round(Decimal(value) / Decimal(10**27), 3)) + "Zm"
    elif value < uni:
        output = str(round(Decimal(value) / Decimal(10**30), 3)) + "Ym"
    elif value < uni * (10**3):
        output = str(round(Decimal(value) / uni, 3)) + "uni"
    elif value < uni * (10**6):
        output = str(round(Decimal(value) / uni / Decimal(10**3), 3)) + "kuni"
    elif value < uni * (10**9):
        output = str(round(Decimal(value) / uni / Decimal(10**6), 3)) + "Muni"
    elif value < uni * (10**12):
        output = str(round(Decimal(value) / uni / Decimal(10**9), 3)) + "Guni"
    elif value < uni * (10**15):
        output = str(round(Decimal(value) / uni / Decimal(10**12), 3)) + "Tuni"
    elif value < uni * (10**18):
        output = str(round(Decimal(value) / uni / Decimal(10**15), 3)) + "Puni"
    elif value < uni * (10**21):
        output = str(round(Decimal(value) / uni / Decimal(10**18), 3)) + "Euni"
    elif value < uni * (10**24):
        output = str(round(Decimal(value) / uni / Decimal(10**21), 3)) + "Zuni"
    elif value < uni * (10**27):
        output = str(round(Decimal(value) / uni / Decimal(10**24), 3)) + "Yuni"
    else:
        return "∞"
    return output

#Convert 'size values' to a more readable format (USA).
def fromSVUSA(value):
    value = float(value)
    output = ""
    if value <= 0:
        return "0"
    elif value < foot:
        output = str(round(Decimal(value) / inch, 2)) + "in"
    elif value < mile:
        feet = floor(Decimal(value) / foot)
        fulloninches = round(Decimal(value) / inch, 2)
        feettoinches = feet * Decimal(12)
        inches = fulloninches - feettoinches
        output = str(feet) + "'" + str(inches) + "\""
    elif value < au:
        output = str(round(Decimal(value) / mile, 2)) + "mi"
    elif value < ly:
        output = str(round(Decimal(value) / au, 2)) + "AU"
    elif value < uni / 10:
        output = str(round(Decimal(value) / ly, 2)) + "ly"
    elif value < uni * (10**3):
        output = str(round(Decimal(value) / uni, 2)) + "uni"
    elif value < uni * (10**6):
        output = str(round(Decimal(value) / uni / Decimal(10**3), 2)) + "kuni"
    elif value < uni * (10**9):
        output = str(round(Decimal(value) / uni / Decimal(10**6), 2)) + "Muni"
    elif value < uni * (10**12):
        output = str(round(Decimal(value) / uni / Decimal(10**9), 2)) + "Guni"
    elif value < uni * (10**15):
        output = str(round(Decimal(value) / uni / Decimal(10**12), 2)) + "Tuni"
    elif value < uni * (10**18):
        output = str(round(Decimal(value) / uni / Decimal(10**15), 2)) + "Puni"
    elif value < uni * (10**21):
        output = str(round(Decimal(value) / uni / Decimal(10**18), 2)) + "Euni"
    elif value < uni * (10**24):
        output = str(round(Decimal(value) / uni / Decimal(10**21), 2)) + "Zuni"
    elif value < uni * (10**27):
        output = str(round(Decimal(value) / uni / Decimal(10**24), 2)) + "Yuni"
    else:
        return "∞"
    return removedecimals(output)

#Convert any supported weight to 'weight value', or milligrams.
def toWV(value, unit):
    unit = unit.lower()
    if (unit == "yoctograms" or unit == "yoctograms" or unit == "yg"):
        output = Decimal(value) / Decimal(10**21)
    elif (unit == "zeptograms" or unit == "zeptograms" or unit == "zg"):
        output = Decimal(value) / Decimal(10**18)
    elif (unit == "attograms" or unit == "attogram" or unit == "ag"):
        output = Decimal(value) / Decimal(10**15)
    elif (unit == "femtogram" or unit == "femtogram" or unit == "fg"):
        output = Decimal(value) / Decimal(10**12)
    elif (unit == "picogram" or unit == "picogram" or unit == "pg"):
        output = Decimal(value) / Decimal(10**9)
    elif (unit == "nanogram" or unit == "nanogram" or unit == "ng"):
        output = Decimal(value) / Decimal(10**6)
    elif (unit == "microgram" or unit == "microgram" or unit == "ug"):
        output = Decimal(value) / Decimal(10**3)
    elif (unit == "milligrams" or unit == "milligram" or unit == "mg"):
        output = Decimal(value)
    elif (unit == "grams" or unit == "gram" or unit == "g"):
        output = Decimal(value) * Decimal(10**3)
    elif (unit == "kilograms" or unit == "kilogram" or unit == "kg"):
        output = Decimal(value) * Decimal(10**6)
    elif (unit == "megagrams" or unit == "megagram" or unit == "t" or unit == "ton" or unit == "tons" or unit == "tonnes" or unit == "tons"):
        output = Decimal(value) * Decimal(10**9)
    elif (unit == "gigagrams" or unit == "gigagram" or unit == "gg" or unit == "kilotons" or unit == "kiloton" or unit == "kilotonnes" or unit == "kilotonne" or unit == "kt"):
        output = Decimal(value) * Decimal(10**12)
    elif (unit == "teragrams" or unit == "teragram" or unit == "tg" or unit == "megatons" or unit == "megaton" or unit == "megatonnes" or unit == "megatonne" or unit == "mt"):
        output = Decimal(value) * Decimal(10**15)
    elif (unit == "petagrams" or unit == "petagram" or unit == "gigatons" or unit == "gigaton" or unit == "gigatonnes" or unit == "gigatonnes" or unit == "gt"):
        output = Decimal(value) * Decimal(10**18)
    elif (unit == "exagrams" or unit == "exagram" or unit == "eg" or unit == "teratons" or unit == "teraton" or unit == "teratonnes" or unit == "teratonne" or unit == "tt"):
        output = Decimal(value) * Decimal(10**21)
    elif (unit == "zettagrams" or unit == "zettagram" or unit == "petatons" or unit == "petaton" or unit == "petatonnes" or unit == "petatonne" or unit == "pt"):
        output = Decimal(value) * Decimal(10**24)
    elif (unit == "yottagrams" or unit == "yottagram" or unit == "exatons" or unit == "exaton" or unit == "exatonnes" or unit == "exatonne" or unit == "et"):
        output = Decimal(value) * Decimal(10**27)
    elif (unit == "zettatons" or unit == "zettaton" or unit == "zettatonnes" or unit == "zettatonne" or unit == "zt"):
        output = Decimal(value) * Decimal(10**30)
    elif (unit == "yottatons" or unit == "yottaton" or unit == "yottatonnes" or unit == "yottatonne" or unit == "yt"):
        output = Decimal(value) * Decimal(10**33)
    elif (unit == "universes" or unit == "universe" or unit == "uni"):
        output = Decimal(value) * uniw
    elif (unit == "kilouniverses" or unit == "kilouniverse" or unit == "kuni"):
        output = Decimal(value) * uniw * Decimal(10**3)
    elif (unit == "megauniverses" or unit == "megauniverse" or unit == "muni"):
        output = Decimal(value) * uniw * Decimal(10**6)
    elif (unit == "gigauniverses" or unit == "gigauniverse" or unit == "guni"):
        output = Decimal(value) * uniw * Decimal(10**9)
    elif (unit == "terauniverses" or unit == "terauniverse" or unit == "tuni"):
        output = Decimal(value) * uniw * Decimal(10**12)
    elif (unit == "petauniverses" or unit == "petauniverse" or unit == "puni"):
        output = Decimal(value) * uniw * Decimal(10**15)
    elif (unit == "exauniverses" or unit == "exauniverse" or unit == "euni"):
        output = Decimal(value) * uniw * Decimal(10**18)
    elif (unit == "zettauniverses" or unit == "zettauniverse" or unit == "zuni"):
        output = Decimal(value) * uniw * Decimal(10**21)
    elif (unit == "yottauniverses" or unit == "yottauniverse" or unit == "yuni"):
        output = Decimal(value) * uniw * Decimal(10**24)
    elif (unit == "ounces" or unit == "ounce" or unit == "oz"):
        output = Decimal(value) * ounce
    elif (unit == "pounds" or unit == "pound" or unit == "lb" or unit == "lbs"):
        output = Decimal(value) * pound
    elif (unit == "earth" or unit == "earths"):
        output = Decimal(value) * earth
    elif (unit == "sun" or unit == "suns"):
        output = Decimal(value) * sun
    else:
        return None
    return output

#Convert 'weight values' to a more readable format.
def fromWV(value):
    value = Decimal(value)
    if value <= 0:
        return "0"
    elif value < 0.000000000000000001:
        output = str(round(Decimal(value) * Decimal(10**21), 1)) + "yg"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), 1)) + "zg"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), 1)) + "ag"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), 1)) + "fg"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), 1)) + "pg"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), 1)) + "ng"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), 1)) + "µg"
    elif value < 1000:
        output = str(Decimal(value)) + "mg"
    elif value < 10000000:
        output = str(round(Decimal(value) / Decimal(10**3), 1)) + "g"
    elif value < 1000000000:
        output = str(round(Decimal(value) / Decimal(10**6), 1)) + "kg"
    elif value < 100000000000:
        output = str(round(Decimal(value) / Decimal(10**9), 1)) + "t"
    elif value < 100000000000000:
        output = str(round(Decimal(value) / Decimal(10**12), 1)) + "kt"
    elif value < 100000000000000000:
        output = str(round(Decimal(value) / Decimal(10**15), 1)) + "Mt"
    elif value < 100000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**18), 1)) + "Gt"
    elif value < 100000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**21), 1)) + "Tt"
    elif value < 100000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**24), 1)) + "Pt"
    elif value < 100000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**27), 1)) + "Et"
    elif value < 100000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**30), 1)) + "Zt"
    elif value < 100000000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**33), 1)) + "Yt"
    elif value < uniw * (10**3):
        output = str(round(Decimal(value) / uniw, 1)) + "uni"
    elif value < uniw * (10**6):
        output = str(round(Decimal(value) / uniw / Decimal(10**3), 1)) + "kuni"
    elif value < uniw * (10**9):
        output = str(round(Decimal(value) / uniw / Decimal(10**6), 1)) + "Muni"
    elif value < uniw * (10**12):
        output = str(round(Decimal(value) / uniw / Decimal(10**9), 1)) + "Guni"
    elif value < uniw * (10**15):
        output = str(round(Decimal(value) / uniw / Decimal(10**12), 1)) + "Tuni"
    elif value < uniw * (10**18):
        output = str(round(Decimal(value) / uniw / Decimal(10**15), 1)) + "Puni"
    elif value < uniw * (10**21):
        output = str(round(Decimal(value) / uniw / Decimal(10**18), 1)) + "Euni"
    elif value < uniw * (10**24):
        output = str(round(Decimal(value) / uniw / Decimal(10**21), 1)) + "Zuni"
    elif value < uniw * (10**27):
        output = str(round(Decimal(value) / uniw / Decimal(10**24), 1)) + "Yuni"
    else:
        return "∞"
    return output

#Convert 'weight values' to a more readable format (USA).
def fromWVUSA(value):
    value = Decimal(value)
    if value == 0:
        return "almost nothing"
    elif value < pound:
        output = str(place_value(round(Decimal(value) / ounce, 1))) + "oz"
    elif value < uston:
        output = str(place_value(round(Decimal(value) / pound, 1))) + "lb"
    elif value < earth / 10:
        output = str(place_value(round(Decimal(value) / uston, 1))) + " US tons"
    elif value < sun / 10:
        output = str(place_value(round(Decimal(value) / earth, 1))) + " Earths"
    elif value < milkyway:
        output = str(place_value(round(Decimal(value) / sun, 1))) + " Suns"
    elif value < uniw:
        output = str(place_value(round(Decimal(value) / milkyway, 1))) + " Milky Ways"
    elif value < uniw * (10**3):
        output = str(round(Decimal(value) / uniw, 1)) + "uni"
    elif value < uniw * (10**6):
        output = str(round(Decimal(value) / uniw / Decimal(10**3), 1)) + "kuni"
    elif value < uniw * (10**9):
        output = str(round(Decimal(value) / uniw / Decimal(10**6), 1)) + "Muni"
    elif value < uniw * (10**12):
        output = str(round(Decimal(value) / uniw / Decimal(10**9), 1)) + "Guni"
    elif value < uniw * (10**15):
        output = str(round(Decimal(value) / uniw / Decimal(10**12), 1)) + "Tuni"
    elif value < uniw * (10**18):
        output = str(round(Decimal(value) / uniw / Decimal(10**15), 1)) + "Puni"
    elif value < uniw * (10**21):
        output = str(round(Decimal(value) / uniw / Decimal(10**18), 1)) + "Euni"
    elif value < uniw * (10**24):
        output = str(round(Decimal(value) / uniw / Decimal(10**21), 1)) + "Zuni"
    elif value < uniw * (10**27):
        output = str(round(Decimal(value) / uniw / Decimal(10**24), 1)) + "Yuni"
    else:
        return "∞"
    return output

def toCV(size):
    size = size.upper()
    if size == "AA" or size == "AAA":
        return "0.5"
    firstlet = str(ord(size[0])&31)
    extraletters = len(size) - 1
    return str(int(firstlet) + extraletters)

def fromCV(value):
    if value == "0.5":
        return "AA"
    elif int(value) > 0.5 and int(value) <= 26:
        answer = chr(int(value) + 64)
        if answer == "E":
            answer = "DD / E"
        if answer == "F":
            answer = "DDD / F"
    elif int(value) > 26:
        return "Z" * (int(value) - 25)

def toShoeSize(sv):
    inches = Decimal(sv) / inch
    shoesize = 3 * inches
    shoesize = shoesize - 22
    shoesize = place_value(round_nearest_half(shoesize))
    return shoesize

def fromShoeSize(size):
    inches = Decimal(size) + 22
    inches = inches / Decimal(3)
    out = inches * inch
    return out

def check(ctx):
#Disable commands for users with the SizeBot_Banned role.
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None
