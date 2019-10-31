import discord
from discord.ext import commands
import re
import datetime
from datetime import *
import time
from time import strftime, localtime
import sys
import os
import math
from math import *
import random
from decimal import *
from colored import fore, back, style, fg, bg, attr
from pathlib import Path
import string
import traceback
import asyncio
import codecs
import digilogger as logger


# TODO: Make this do something useful.
class DigiException(Exception):
    pass


# Version.
version = "3.3.7"

# Defaults
defaultheight = Decimal(1754000)  # micrometers
defaultweight = Decimal(66760000)  # milligrams
defaultdensity = Decimal(1.0)

# Constants
newline = "\n"
folder = ".."
reol = 106871675617820672
sizebot_id = 344590087679639556
digiid = 271803699095928832
yukioid = 140162671445147648
mee6id = 553792568824037386
sizebotuser_roleid = 562356758522101769
brackets = ["[", "]", "<", ">"]
allowbrackets = ("&compare", "&stats")

# Array item names.
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7


def regenhexcode():
    # 16-char hex string gen for unregister.
    hexdigits = "1234567890abcdef"
    lst = [random.choice(hexdigits) for n in range(16)]
    hexstring = "".join(lst)
    hexfile = open("../hexstring.txt", "w")
    hexfile.write(hexstring)
    hexfile.close()


def readhexcode():
    # Read the hexcode from the file.
    hexfile = open("../hexstring.txt", "r")
    hexcode = hexfile.readlines()
    hexfile.close()
    return str(hexcode[0])


# ASCII art.
ascii = r"""
. _____ _        ______       _   _____ .
./  ___(_)       | ___ \     | | |____ |.
.\ `--. _ _______| |_/ / ___ | |_    / /.
. `--. \ |_  / _ \ ___ \/ _ \| __|   \ \.
./\__/ / |/ /  __/ |_/ / (_) | |_.___/ /.
.\____/|_/___\___\____/ \___/ \__\____/ ."""

# Configure decimal module.
getcontext()
context = Context(prec=100, rounding=ROUND_HALF_EVEN, Emin=-9999999, Emax=999999,
                  capitals=1, clamp=0, flags=[], traps=[Overflow, DivisionByZero,
                                                        InvalidOperation])
setcontext(context)


# Get number from string.
def getnum(string):
    match = re.search(r"\d+\.?\d*", string)
    if match is None:
        return None
    return Decimal(match.group(0))


# Get letters from string.
def getlet(string):
    match = re.search(r"[a-zA-Z\'\"]+", string)
    if match is None:
        return None
    return match.group(0)


# Remove decimals.
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

def removebrackets(string):
    for bracket in brackets:
        string = string.replace(bracket, "")
    return string


def round_nearest_half(number):
    return round(number * 2) / 2


def place_value(number):
    return ("{:,}".format(number))


def pretty_time_delta(seconds):
    seconds = int(seconds)
    years, seconds = divmod(seconds, 86400 * 365)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if years > 0:
        return '%d years, %d days, %d hours, %d minutes, %d seconds' % (years, days, hours, minutes, seconds)
    elif days > 0:
        return '%d days, %d hours, %d minutes, %d seconds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%d hours, %d minutes, %d seconds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%d minutes, %d seconds' % (minutes, seconds)
    else:
        return '%d seconds' % (seconds)


# Update users nicknames to include sizetags.
async def nickupdate(user):
    if user.discriminator == "0000": return
    if not isinstance(user, discord.Member):
        if user.id == mee6id: return
        logger.warn(f"Attempted to update user {user.id} ({user.name}), but they DM'd SizeBot.")
    # Don't update owner's nick, permissions error.
    if user.id == user.guild.owner.id:
        # logger.warn(f"Attempted to update user {user.id} ({user.name}), but they own this server.")
        return
    # Don't update users who aren't registered.
    if not os.path.exists(f"{folder}/users/{user.id}.txt"):
        return

    userarray = read_user(user.id)

    # User's display setting is N. No sizetag.
    if userarray[DISP].strip() != "Y":
        return

    height = userarray[CHEI]
    if height is None:
        height = userarray[BHEI]
    nick = userarray[NICK].strip()
    species = userarray[SPEC].strip()

    unit_system = userarray[UNIT].strip().upper()
    if unit_system == "M":
        sizetag = fromSV(height)
    elif unit_system == "U":
        sizetag = fromSVUSA(height)
    else:
        sizetag = ""

    if species != "None":
        sizetag = f"{sizetag}, {species}"

    max_nick_len = 32

    if len(nick) > max_nick_len:
        # User has set their nick too large. Truncate.
        nick = nick[:max_nick_len]

    if len(nick) + len(sizetag) + 3 <= max_nick_len:
        # Fit full nick and sizetag.
        newnick = f"{nick} [{sizetag}]"
    elif len(sizetag) + 7 <= max_nick_len:
        # Fit short nick and sizetag.
        chars_left = max_nick_len - len(sizetag) - 4
        short_nick = nick[:chars_left]
        newnick = f"{short_nick}… [{sizetag}]"
    else:
        # Cannot fit the new sizetag.
        newnick = nick
    try:
        await user.edit(nick=newnick)
    except discord.Forbidden:
        logger.crit(f"Tried to nickupdate {user.id} ({user.name}), but it is forbidden!")
        return


    #logger.msg(f"Updated user {user.id} ({user.name}).")


# Read in specific user.
def read_user(user_id):
    user_id = str(user_id)
    userfile = folder + "/users/" + user_id + ".txt"
    with open(userfile) as f:
        # Make array of lines from file.
        content = f.readlines()
        if content == []: os.remove(userfile)
        # Replace None.
        if content[BWEI] == "None" + newline:
            content[BWEI] = str(defaultweight) + newline
        if content[BHEI] == "None" + newline:
            content[BHEI] = str(defaultweight) + newline
        if content[CHEI] == "None" + newline:
            content[CHEI] = content[3]
        # Round all values to 18 decimal places.
        content[CHEI] = str(round(float(content[CHEI]), 18))
        content[BHEI] = str(round(float(content[BHEI]), 18))
        content[BWEI] = str(round(float(content[BWEI]), 18))
        return content


def read_userline(user_id, line):
    content = read_user(user_id)
    return content[line - 1]


# Write to specific user.
def write_user(user_id, content):
    user_id = str(user_id)
    # Replace None.
    if content[BWEI] == "None" + newline:
        content[BWEI] = str(defaultweight) + newline
    if content[BHEI] == "None" + newline:
        content[BHEI] = str(defaultweight) + newline
    if content[CHEI] == "None" + newline:
        content[CHEI] = content[3]
    # Round all values to 18 decimal places.
    content[CHEI] = str(round(float(content[CHEI]), 18))
    content[BHEI] = str(round(float(content[BHEI]), 18))
    content[BWEI] = str(round(float(content[BWEI]), 18))
    # Add new line characters to entries that don't have them.
    for idx, item in enumerate(content):
        if not content[idx].endswith("\n"):
            content[idx] = content[idx] + "\n"
    # Delete userfile.
    os.remove(folder + "/users/" + user_id + ".txt")
    # Make a new userfile.
    userfile = open(folder + "/users/" + user_id + ".txt", "w+")
    # Write content to lines.
    userfile.writelines(content)


def isFeetAndInchesAndIfSoFixIt(input):
    regex = r"^(?P<feet>\d+(ft|foot|feet|\'))(?P<inch>\d+(in|\")*)"
    m = re.match(regex, input, flags=re.I)
    if not m:
        return input
    wholefeet = m.group('feet')
    wholeinch = m.group('inch')
    feet = getnum(wholefeet)
    inch = getnum(wholeinch)
    if feet == None: feet = 0
    if inch == None: inch = 0
    totalinches = (feet * 12) + inch
    return f"{totalinches}in"

# Count users.
members = 0
path = folder + '/users'
listing = os.listdir(path)
for infile in listing:
    if infile.endswith(".txt"):
        members += 1
logger.load("Loaded {0} users.".format(members))

enspace = "\u2002"
printtab = enspace * 4


# Slow growth tasks.
tasks = {}

# Unit constants.
# Height [micrometers]
inch = Decimal(25400)
foot = inch * Decimal(12)
mile = foot * Decimal(5280)
ly = mile * Decimal(5879000000000)
au = Decimal(149597870700000000)
uni = Decimal(879848000000000000000000000000000)
infinity = Decimal(879848000000000000000000000000000000000000000000000000000000)
# Weight [milligrams]
ounce = Decimal(28350)
pound = ounce * Decimal(16)
uston = pound * Decimal(2000)
earth = Decimal(5972198600000000000000000000000)
sun = Decimal(1988435000000000000000000000000000000)
milkyway = Decimal(95000000000000000000000000000000000000000000000)
uniw = Decimal(3400000000000000000000000000000000000000000000000000000000000)


# Convert any supported height to 'size value'
def toSV(value, unit):
    if value is None or unit is None:
        return None
    unit = unit.lower()
    if unit in ["yoctometers", "yoctometer"]:
        output = Decimal(value) / Decimal(10**18)
    elif unit in ["zeptometers", "zeptometer"]:
        output = Decimal(value) / Decimal(10**15)
    elif unit in ["attometers", "attometer", "am"]:
        output = Decimal(value) / Decimal(10**12)
    elif unit in ["femtometers", "femtometer", "fm"]:
        output = Decimal(value) / Decimal(10**9)
    elif unit in ["picometers", "picometer"]:
        output = Decimal(value) / Decimal(10**6)
    elif unit in ["nanometers", "nanometer", "nm"]:
        output = Decimal(value) / Decimal(10**3)
    elif unit in ["micrometers", "micrometer", "um"]:
        output = Decimal(value)
    elif unit in ["millimeters", "millimeter", "mm"]:
        output = Decimal(value) * Decimal(10**3)
    elif unit in ["centimeters", "centimeter", "cm"]:
        output = Decimal(value) * Decimal(10**4)
    elif unit in ["meters", "meter", "m"]:
        output = Decimal(value) * Decimal(10**6)
    elif unit in ["kilometers", "kilometer", "km"]:
        output = Decimal(value) * Decimal(10**9)
    elif unit in ["megameters", "megameter"]:
        output = Decimal(value) * Decimal(10**12)
    elif unit in ["gigameters", "gigameter", "gm"]:
        output = Decimal(value) * Decimal(10**15)
    elif unit in ["terameters", "terameter", "tm"]:
        output = Decimal(value) * Decimal(10**18)
    elif unit in ["petameters", "petameter", "pm"]:
        output = Decimal(value) * Decimal(10**21)
    elif unit in ["exameters", "exameter", "em"]:
        output = Decimal(value) * Decimal(10**24)
    elif unit in ["zettameters", "zettameter", "zm"]:
        output = Decimal(value) * Decimal(10**27)
    elif unit in ["yottameters", "yottameter", "ym"]:
        output = Decimal(value) * Decimal(10**30)
    elif unit in ["inches", "inch", "in", "\""]:
        output = Decimal(value) * inch
    elif unit in ["feet", "foot", "ft", "\'"]:
        output = Decimal(value) * foot
    elif unit in ["miles", "mile", "mi"]:
        output = Decimal(value) * mile
    elif unit in ["lightyears", "lightyear", "ly"]:
        output = Decimal(value) * ly
    elif unit in ["astronomical_units", "astronomical_unit", "au"]:
        output = Decimal(value) * au
    elif unit in ["universes", "universe", "uni"]:
        output = Decimal(value) * uni
    elif unit in ["kilouniverses", "kilouniverse", "kuni"]:
        output = Decimal(value) * uni * Decimal(10**3)
    elif unit in ["megauniverses", "megauniverse", "muni"]:
        output = Decimal(value) * uni * Decimal(10**6)
    elif unit in ["gigauniverses", "gigauniverse", "guni"]:
        output = Decimal(value) * uni * Decimal(10**9)
    elif unit in ["terauniverses", "terauniverse", "tuni"]:
        output = Decimal(value) * uni * Decimal(10**12)
    elif unit in ["petauniverses", "petauniverse", "puni"]:
        output = Decimal(value) * uni * Decimal(10**15)
    elif unit in ["exauniverses", "exauniverse", "euni"]:
        output = Decimal(value) * uni * Decimal(10**18)
    elif unit in ["zettauniverses", "zettauniverse", "zuni"]:
        output = Decimal(value) * uni * Decimal(10**21)
    elif unit in ["yottauniverses", "yottauniverse", "yuni"]:
        output = Decimal(value) * uni * Decimal(10**24)
    else:
        return None
    return output


# Convert 'size values' to a more readable format (metric).
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
    elif value < 10**2:
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


# Convert 'size values' to a more readable format (accurate).
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


# Convert 'size values' to a more readable format (USA).
def fromSVUSA(value):
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
    elif value < 10**2:
        output = str(round(Decimal(value), 2)) + "µm"
    elif value < 10**4:
        output = str(round(Decimal(value) / Decimal(10**3), 2)) + "mm"
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


# Convert any supported weight to 'weight value', or milligrams.
def toWV(value, unit):
    unit = unit.lower()
    if unit in ["yoctograms", "yoctograms", "yg"]:
        output = Decimal(value) / Decimal(10**21)
    elif unit in ["zeptograms", "zeptograms", "zg"]:
        output = Decimal(value) / Decimal(10**18)
    elif unit in ["attograms", "attogram", "ag"]:
        output = Decimal(value) / Decimal(10**15)
    elif unit in ["femtogram", "femtogram", "fg"]:
        output = Decimal(value) / Decimal(10**12)
    elif unit in ["picogram", "picogram", "pg"]:
        output = Decimal(value) / Decimal(10**9)
    elif unit in ["nanogram", "nanogram", "ng"]:
        output = Decimal(value) / Decimal(10**6)
    elif unit in ["microgram", "microgram", "ug"]:
        output = Decimal(value) / Decimal(10**3)
    elif unit in ["milligrams", "milligram", "mg"]:
        output = Decimal(value)
    elif unit in ["grams", "gram", "g"]:
        output = Decimal(value) * Decimal(10**3)
    elif unit in ["kilograms", "kilogram", "kg"]:
        output = Decimal(value) * Decimal(10**6)
    elif unit in ["megagrams", "megagram", "t", "ton", "tons", "tonnes", "tons"]:
        output = Decimal(value) * Decimal(10**9)
    elif unit in ["gigagrams", "gigagram", "gg", "kilotons", "kiloton", "kilotonnes", "kilotonne", "kt"]:
        output = Decimal(value) * Decimal(10**12)
    elif unit in ["teragrams", "teragram", "tg", "megatons", "megaton", "megatonnes", "megatonne", "mt"]:
        output = Decimal(value) * Decimal(10**15)
    elif unit in ["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes", "gt"]:
        output = Decimal(value) * Decimal(10**18)
    elif unit in ["exagrams", "exagram", "eg", "teratons", "teraton", "teratonnes", "teratonne", "tt"]:
        output = Decimal(value) * Decimal(10**21)
    elif unit in ["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne", "pt"]:
        output = Decimal(value) * Decimal(10**24)
    elif unit in ["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne", "et"]:
        output = Decimal(value) * Decimal(10**27)
    elif unit in ["zettatons", "zettaton", "zettatonnes", "zettatonne", "zt"]:
        output = Decimal(value) * Decimal(10**30)
    elif unit in ["yottatons", "yottaton", "yottatonnes", "yottatonne", "yt"]:
        output = Decimal(value) * Decimal(10**33)
    elif unit in ["universes", "universe", "uni"]:
        output = Decimal(value) * uniw
    elif unit in ["kilouniverses", "kilouniverse", "kuni"]:
        output = Decimal(value) * uniw * Decimal(10**3)
    elif unit in ["megauniverses", "megauniverse", "muni"]:
        output = Decimal(value) * uniw * Decimal(10**6)
    elif unit in ["gigauniverses", "gigauniverse", "guni"]:
        output = Decimal(value) * uniw * Decimal(10**9)
    elif unit in ["terauniverses", "terauniverse", "tuni"]:
        output = Decimal(value) * uniw * Decimal(10**12)
    elif unit in ["petauniverses", "petauniverse", "puni"]:
        output = Decimal(value) * uniw * Decimal(10**15)
    elif unit in ["exauniverses", "exauniverse", "euni"]:
        output = Decimal(value) * uniw * Decimal(10**18)
    elif unit in ["zettauniverses", "zettauniverse", "zuni"]:
        output = Decimal(value) * uniw * Decimal(10**21)
    elif unit in ["yottauniverses", "yottauniverse", "yuni"]:
        output = Decimal(value) * uniw * Decimal(10**24)
    elif unit in ["ounces", "ounce", "oz"]:
        output = Decimal(value) * ounce
    elif unit in ["pounds", "pound", "lb", "lbs"]:
        output = Decimal(value) * pound
    elif unit in ["earth", "earths"]:
        output = Decimal(value) * earth
    elif unit in ["sun", "suns"]:
        output = Decimal(value) * sun
    else:
        return None
    return output


# Convert 'weight values' to a more readable format.
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
        output = str(round(Decimal(value), 1)) + "mg"
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


# Convert 'weight values' to a more readable format (USA).
def fromWVUSA(value):
    value = Decimal(value)
    if value == 0:
        return "almost nothing"
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
        output = str(round(Decimal(value), 1)) + "mg"
    elif value < (ounce / 10):
        output = str(round(Decimal(value) / Decimal(10**3), 1)) + "g"
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


def toShoeSize(inchamount):
    child = False
    inches = Decimal(inchamount)
    shoesize = 3 * inches
    shoesize = shoesize - 22
    if shoesize < 1:
        child = True
        shoesize += 12 + Decimal(1 / 3)
    if shoesize < 1:
        return "No shoes exist this small!"
    shoesize = place_value(round_nearest_half(shoesize))
    if child:
        shoesize = "Children's " + shoesize
    return "Size US " + shoesize

#Currently unused.
def fromShoeSize(size):
    child = False
    if "c" in size.toLower():
        child = True
    size = getnum(size)
    inches = Decimal(size) + 22
    if child:
        inches = Decimal(size) + 22 - 12 - (1 / 3)
    inches = inches / Decimal(3)
    out = inches * inch
    return out


def check(ctx):
    # Disable commands for users with the SizeBot_Banned role.
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None


logger.load("Global functions loaded.")
