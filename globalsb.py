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
    with open("../hexstring.txt", "w") as hexfile:
        hexfile.write(hexstring)


def readhexcode():
    # Read the hexcode from the file.
    with open("../hexstring.txt", "r") as hexfile:
        hexcode = hexfile.readlines()
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
context = Context(prec=250, rounding=ROUND_HALF_EVEN, Emin=-9999999, Emax=999999,
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
    if user.discriminator == "0000":
        return
    if not isinstance(user, discord.Member):
        if user.id == mee6id:
            return
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
        if content == []:
            os.remove(userfile)
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
    with open(folder + "/users/" + user_id + ".txt", "w+") as userfile:
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
    if feet is None:
        feet = 0
    if inch is None:
        inch = 0
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
    unitlower = unit.lower()
    if unitlower in ["yoctometers", "yoctometer"]:
        output = Decimal(value) / Decimal("1E18")
    elif unitlower in ["zeptometers", "zeptometer"]:
        output = Decimal(value) / Decimal("1E15")
    elif unitlower in ["attometers", "attometer"] or unit == "am":
        output = Decimal(value) / Decimal("1E12")
    elif unitlower in ["femtometers", "femtometer"] or unit == "fm":
        output = Decimal(value) / Decimal("1E9")
    elif unitlower in ["picometers", "picometer"]:
        output = Decimal(value) / Decimal("1E6")
    elif unitlower in ["nanometers", "nanometer"] or unit == "nm":
        output = Decimal(value) / Decimal("1E3")
    elif unitlower in ["micrometers", "micrometer"] or unit == "um":
        output = Decimal(value)
    elif unitlower in ["millimeters", "millimeter"] or unit == "mm":
        output = Decimal(value) * Decimal("1E3")
    elif unitlower in ["centimeters", "centimeter"] or unit == "cm":
        output = Decimal(value) * Decimal("1E4")
    elif unitlower in ["meters", "meter"] or unit == "m":
        output = Decimal(value) * Decimal("1E6")
    elif unitlower in ["kilometers", "kilometer"] or unit == "km":
        output = Decimal(value) * Decimal("1E9")
    elif unitlower in ["megameters", "megameter"]:
        output = Decimal(value) * Decimal("1E12")
    elif unitlower in ["gigameters", "gigameter"] or unit == "gm":
        output = Decimal(value) * Decimal("1E15")
    elif unitlower in ["terameters", "terameter"] or unit == "tm":
        output = Decimal(value) * Decimal("1E18")
    elif unitlower in ["petameters", "petameter"] or unit == "pm":
        output = Decimal(value) * Decimal("1E21")
    elif unitlower in ["exameters", "exameter"] or unit == "em":
        output = Decimal(value) * Decimal("1E24")
    elif unitlower in ["zettameters", "zettameter"] or unit == "zm":
        output = Decimal(value) * Decimal("1E27")
    elif unitlower in ["yottameters", "yottameter"] or unit == "ym":
        output = Decimal(value) * Decimal("1E30")
    elif unitlower in ["inches", "inch", "in", "\""]:
        output = Decimal(value) * inch
    elif unitlower in ["feet", "foot", "ft", "\'"]:
        output = Decimal(value) * foot
    elif unitlower in ["miles", "mile", "mi"]:
        output = Decimal(value) * mile
    elif unitlower in ["lightyears", "lightyear"] or unit == "ly":
        output = Decimal(value) * ly
    elif unitlower in ["astronomical_units", "astronomical_unit"] or unit == "au":
        output = Decimal(value) * au
    elif unitlower in ["universes", "universe"] or unit == "uni":
        output = Decimal(value) * uni
    elif unitlower in ["kilouniverses", "kilouniverse"] or unit == "kuni":
        output = Decimal(value) * uni * Decimal("1E3")
    elif unitlower in ["megauniverses", "megauniverse"] or unit == "muni":
        output = Decimal(value) * uni * Decimal("1E6")
    elif unitlower in ["gigauniverses", "gigauniverse"] or unit == "guni":
        output = Decimal(value) * uni * Decimal("1E9")
    elif unitlower in ["terauniverses", "terauniverse"] or unit == "tuni":
        output = Decimal(value) * uni * Decimal("1E12")
    elif unitlower in ["petauniverses", "petauniverse"] or unit == "puni":
        output = Decimal(value) * uni * Decimal("1E15")
    elif unitlower in ["exauniverses", "exauniverse"] or unit == "euni":
        output = Decimal(value) * uni * Decimal("1E18")
    elif unitlower in ["zettauniverses", "zettauniverse"] or unit == "zuni":
        output = Decimal(value) * uni * Decimal("1E21")
    elif unitlower in ["yottauniverses", "yottauniverse"] or unit == "yuni":
        output = Decimal(value) * uni * Decimal("1E24")
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
        output = str(round(Decimal(value) * Decimal("1E18"), 2)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal("1E15"), 2)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal("1E12"), 2)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal("1E9"), 2)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal("1E6"), 2)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal("1E3"), 2)) + "nm"
    elif value < "1E2":
        output = str(round(Decimal(value), 2)) + "µm"
    elif value < "1E4":
        output = str(round(Decimal(value) / Decimal("1E3"), 2)) + "mm"
    elif value < "1E6":
        output = str(round(Decimal(value) / Decimal("1E4"), 2)) + "cm"
    elif value < "1E9":
        output = str(round(Decimal(value) / Decimal("1E6"), 2)) + "m"
    elif value < "1E12":
        output = str(round(Decimal(value) / Decimal("1E9"), 2)) + "km"
    elif value < "1E15":
        output = str(round(Decimal(value) / Decimal("1E12"), 2)) + "Mm"
    elif value < "1E18":
        output = str(round(Decimal(value) / Decimal("1E15"), 2)) + "Gm"
    elif value < "1E21":
        output = str(round(Decimal(value) / Decimal("1E18"), 2)) + "Tm"
    elif value < "1E24":
        output = str(round(Decimal(value) / Decimal("1E21"), 2)) + "Pm"
    elif value < "1E27":
        output = str(round(Decimal(value) / Decimal("1E24"), 2)) + "Em"
    elif value < "1E30":
        output = str(round(Decimal(value) / Decimal("1E27"), 2)) + "Zm"
    elif value < uni:
        output = str(round(Decimal(value) / Decimal("1E30"), 2)) + "Ym"
    elif value < uni * ("1E3"):
        output = str(round(Decimal(value) / uni, 2)) + "uni"
    elif value < uni * ("1E6"):
        output = str(round(Decimal(value) / uni / Decimal("1E3"), 2)) + "kuni"
    elif value < uni * ("1E9"):
        output = str(round(Decimal(value) / uni / Decimal("1E6"), 2)) + "Muni"
    elif value < uni * ("1E12"):
        output = str(round(Decimal(value) / uni / Decimal("1E9"), 2)) + "Guni"
    elif value < uni * ("1E15"):
        output = str(round(Decimal(value) / uni / Decimal("1E12"), 2)) + "Tuni"
    elif value < uni * ("1E18"):
        output = str(round(Decimal(value) / uni / Decimal("1E15"), 2)) + "Puni"
    elif value < uni * ("1E21"):
        output = str(round(Decimal(value) / uni / Decimal("1E18"), 2)) + "Euni"
    elif value < uni * ("1E24"):
        output = str(round(Decimal(value) / uni / Decimal("1E21"), 2)) + "Zuni"
    elif value < uni * ("1E27"):
        output = str(round(Decimal(value) / uni / Decimal("1E24"), 2)) + "Yuni"
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
        output = str(round(Decimal(value) * Decimal("1E18"), 3)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal("1E15"), 3)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal("1E12"), 3)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal("1E9"), 3)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal("1E6"), 3)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal("1E3"), 3)) + "nm"
    elif value < "1E3":
        output = str(round(Decimal(value), 3)) + "µm"
    elif value < "1E4":
        output = str(round(Decimal(value) / Decimal("1E3"), 3)) + "mm"
    elif value < "1E6":
        output = str(round(Decimal(value) / Decimal("1E4"), 3)) + "cm"
    elif value < "1E9":
        output = str(round(Decimal(value) / Decimal("1E6"), 3)) + "m"
    elif value < "1E12":
        output = str(round(Decimal(value) / Decimal("1E9"), 3)) + "km"
    elif value < "1E15":
        output = str(round(Decimal(value) / Decimal("1E12"), 3)) + "Mm"
    elif value < "1E18":
        output = str(round(Decimal(value) / Decimal("1E15"), 3)) + "Gm"
    elif value < "1E21":
        output = str(round(Decimal(value) / Decimal("1E18"), 3)) + "Tm"
    elif value < "1E24":
        output = str(round(Decimal(value) / Decimal("1E21"), 3)) + "Pm"
    elif value < "1E27":
        output = str(round(Decimal(value) / Decimal("1E24"), 3)) + "Em"
    elif value < "1E30":
        output = str(round(Decimal(value) / Decimal("1E27"), 3)) + "Zm"
    elif value < uni:
        output = str(round(Decimal(value) / Decimal("1E30"), 3)) + "Ym"
    elif value < uni * ("1E3"):
        output = str(round(Decimal(value) / uni, 3)) + "uni"
    elif value < uni * ("1E6"):
        output = str(round(Decimal(value) / uni / Decimal("1E3"), 3)) + "kuni"
    elif value < uni * ("1E9"):
        output = str(round(Decimal(value) / uni / Decimal("1E6"), 3)) + "Muni"
    elif value < uni * ("1E12"):
        output = str(round(Decimal(value) / uni / Decimal("1E9"), 3)) + "Guni"
    elif value < uni * ("1E15"):
        output = str(round(Decimal(value) / uni / Decimal("1E12"), 3)) + "Tuni"
    elif value < uni * ("1E18"):
        output = str(round(Decimal(value) / uni / Decimal("1E15"), 3)) + "Puni"
    elif value < uni * ("1E21"):
        output = str(round(Decimal(value) / uni / Decimal("1E18"), 3)) + "Euni"
    elif value < uni * ("1E24"):
        output = str(round(Decimal(value) / uni / Decimal("1E21"), 3)) + "Zuni"
    elif value < uni * ("1E27"):
        output = str(round(Decimal(value) / uni / Decimal("1E24"), 3)) + "Yuni"
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
        output = str(round(Decimal(value) * Decimal("1E18"), 2)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal("1E15"), 2)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal("1E12"), 2)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal("1E9"), 2)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal("1E6"), 2)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal("1E3"), 2)) + "nm"
    elif value < "1E2":
        output = str(round(Decimal(value), 2)) + "µm"
    elif value < "1E4":
        output = str(round(Decimal(value) / Decimal("1E3"), 2)) + "mm"
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
    elif value < uni * ("1E3"):
        output = str(round(Decimal(value) / uni, 2)) + "uni"
    elif value < uni * ("1E6"):
        output = str(round(Decimal(value) / uni / Decimal("1E3"), 2)) + "kuni"
    elif value < uni * ("1E9"):
        output = str(round(Decimal(value) / uni / Decimal("1E6"), 2)) + "Muni"
    elif value < uni * ("1E12"):
        output = str(round(Decimal(value) / uni / Decimal("1E9"), 2)) + "Guni"
    elif value < uni * ("1E15"):
        output = str(round(Decimal(value) / uni / Decimal("1E12"), 2)) + "Tuni"
    elif value < uni * ("1E18"):
        output = str(round(Decimal(value) / uni / Decimal("1E15"), 2)) + "Puni"
    elif value < uni * ("1E21"):
        output = str(round(Decimal(value) / uni / Decimal("1E18"), 2)) + "Euni"
    elif value < uni * ("1E24"):
        output = str(round(Decimal(value) / uni / Decimal("1E21"), 2)) + "Zuni"
    elif value < uni * ("1E27"):
        output = str(round(Decimal(value) / uni / Decimal("1E24"), 2)) + "Yuni"
    else:
        return "∞"
    return removedecimals(output)


# Convert any supported weight to 'weight value', or milligrams.
def toWV(value, unit):
    unitlower = unit.lower()
    if unitlower in ["yoctograms", "yoctograms"] or unit == "yg":
        output = Decimal(value) / Decimal("1E21")
    elif unitlower in ["zeptograms", "zeptograms"] or unit == "zg":
        output = Decimal(value) / Decimal("1E18")
    elif unitlower in ["attograms", "attogram"] or unit == "ag":
        output = Decimal(value) / Decimal("1E15")
    elif unitlower in ["femtogram", "femtogram"] or unit == "fg":
        output = Decimal(value) / Decimal("1E12")
    elif unitlower in ["picogram", "picogram"] or unit == "pg":
        output = Decimal(value) / Decimal("1E9")
    elif unitlower in ["nanogram", "nanogram"] or unit == "ng":
        output = Decimal(value) / Decimal("1E6")
    elif unitlower in ["microgram", "microgram"] or unit == "ug":
        output = Decimal(value) / Decimal("1E3")
    elif unitlower in ["milligrams", "milligram"] or unit == "mg":
        output = Decimal(value)
    elif unitlower in ["grams", "gram"] or unit == "g":
        output = Decimal(value) * Decimal("1E3")
    elif unitlower in ["kilograms", "kilogram"] or unit == "kg":
        output = Decimal(value) * Decimal("1E6")
    elif unitlower in ["megagrams", "megagram", "ton", "tons", "tonnes", "tons"] or unit == "t":
        output = Decimal(value) * Decimal("1E9")
    elif unitlower in ["gigagrams", "gigagram", "kilotons", "kiloton", "kilotonnes", "kilotonne"] or unit in ["gg", "kt"]:
        output = Decimal(value) * Decimal("1E12")
    elif unitlower in ["teragrams", "teragram", "megatons", "megaton", "megatonnes", "megatonne"] or unit in ["tg", "mt"]:
        output = Decimal(value) * Decimal("1E15")
    elif unitlower in ["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes"] or unit == "gt":
        output = Decimal(value) * Decimal("1E18")
    elif unitlower in ["exagrams", "exagram", "teratons", "teraton", "teratonnes", "teratonne"] or unit == ["eg", "tt"]:
        output = Decimal(value) * Decimal("1E21")
    elif unitlower in ["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne"] or unit == "pt":
        output = Decimal(value) * Decimal("1E24")
    elif unitlower in ["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne"] or unit == "et":
        output = Decimal(value) * Decimal("1E27")
    elif unitlower in ["zettatons", "zettaton", "zettatonnes", "zettatonne"] or unit == "zt":
        output = Decimal(value) * Decimal("1E30")
    elif unitlower in ["yottatons", "yottaton", "yottatonnes", "yottatonne"] or unit == "yt":
        output = Decimal(value) * Decimal("1E33")
    elif unitlower in ["universes", "universe"] or unit == "uni":
        output = Decimal(value) * uniw
    elif unitlower in ["kilouniverses", "kilouniverse"] or unit == "kuni":
        output = Decimal(value) * uniw * Decimal("1E3")
    elif unitlower in ["megauniverses", "megauniverse"] or unit == "muni":
        output = Decimal(value) * uniw * Decimal("1E6")
    elif unitlower in ["gigauniverses", "gigauniverse"] or unit == "guni":
        output = Decimal(value) * uniw * Decimal("1E9")
    elif unitlower in ["terauniverses", "terauniverse"] or unit == "tuni":
        output = Decimal(value) * uniw * Decimal("1E12")
    elif unitlower in ["petauniverses", "petauniverse"] or unit == "puni":
        output = Decimal(value) * uniw * Decimal("1E15")
    elif unitlower in ["exauniverses", "exauniverse"] or unit == "euni":
        output = Decimal(value) * uniw * Decimal("1E18")
    elif unitlower in ["zettauniverses", "zettauniverse"] or unit == "zuni":
        output = Decimal(value) * uniw * Decimal("1E21")
    elif unitlower in ["yottauniverses", "yottauniverse"] or unit == "yuni":
        output = Decimal(value) * uniw * Decimal("1E24")
    elif unitlower in ["ounces", "ounce"] or unit == "oz":
        output = Decimal(value) * ounce
    elif unitlower in ["pounds", "pound"] or unit in ["lb", "lbs"]:
        output = Decimal(value) * pound
    elif unitlower in ["earth", "earths"]:
        output = Decimal(value) * earth
    elif unitlower in ["sun", "suns"]:
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
        output = str(round(Decimal(value) * Decimal("1E21"), 1)) + "yg"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal("1E18"), 1)) + "zg"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal("1E15"), 1)) + "ag"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal("1E12"), 1)) + "fg"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal("1E9"), 1)) + "pg"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal("1E6"), 1)) + "ng"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal("1E3"), 1)) + "µg"
    elif value < 1000:
        output = str(round(Decimal(value), 1)) + "mg"
    elif value < 10000000:
        output = str(round(Decimal(value) / Decimal("1E3"), 1)) + "g"
    elif value < 1000000000:
        output = str(round(Decimal(value) / Decimal("1E6"), 1)) + "kg"
    elif value < 100000000000:
        output = str(round(Decimal(value) / Decimal("1E9"), 1)) + "t"
    elif value < 100000000000000:
        output = str(round(Decimal(value) / Decimal("1E12"), 1)) + "kt"
    elif value < 100000000000000000:
        output = str(round(Decimal(value) / Decimal("1E15"), 1)) + "Mt"
    elif value < 100000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E18"), 1)) + "Gt"
    elif value < 100000000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E21"), 1)) + "Tt"
    elif value < 100000000000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E24"), 1)) + "Pt"
    elif value < 100000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E27"), 1)) + "Et"
    elif value < 100000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E30"), 1)) + "Zt"
    elif value < 100000000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal("1E33"), 1)) + "Yt"
    elif value < uniw * ("1E3"):
        output = str(round(Decimal(value) / uniw, 1)) + "uni"
    elif value < uniw * ("1E6"):
        output = str(round(Decimal(value) / uniw / Decimal("1E3"), 1)) + "kuni"
    elif value < uniw * ("1E9"):
        output = str(round(Decimal(value) / uniw / Decimal("1E6"), 1)) + "Muni"
    elif value < uniw * ("1E12"):
        output = str(round(Decimal(value) / uniw / Decimal("1E9"), 1)) + "Guni"
    elif value < uniw * ("1E15"):
        output = str(round(Decimal(value) / uniw / Decimal("1E12"), 1)) + "Tuni"
    elif value < uniw * ("1E18"):
        output = str(round(Decimal(value) / uniw / Decimal("1E15"), 1)) + "Puni"
    elif value < uniw * ("1E21"):
        output = str(round(Decimal(value) / uniw / Decimal("1E18"), 1)) + "Euni"
    elif value < uniw * ("1E24"):
        output = str(round(Decimal(value) / uniw / Decimal("1E21"), 1)) + "Zuni"
    elif value < uniw * ("1E27"):
        output = str(round(Decimal(value) / uniw / Decimal("1E24"), 1)) + "Yuni"
    else:
        return "∞"
    return output


# Convert 'weight values' to a more readable format (USA).
def fromWVUSA(value):
    value = Decimal(value)
    if value == 0:
        return "almost nothing"
    elif value < 0.000000000000000001:
        output = str(round(Decimal(value) * Decimal("1E21"), 1)) + "yg"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal("1E18"), 1)) + "zg"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal("1E15"), 1)) + "ag"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal("1E12"), 1)) + "fg"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal("1E9"), 1)) + "pg"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal("1E6"), 1)) + "ng"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal("1E3"), 1)) + "µg"
    elif value < 1000:
        output = str(round(Decimal(value), 1)) + "mg"
    elif value < (ounce / 10):
        output = str(round(Decimal(value) / Decimal("1E3"), 1)) + "g"
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
    elif value < uniw * ("1E3"):
        output = str(round(Decimal(value) / uniw, 1)) + "uni"
    elif value < uniw * ("1E6"):
        output = str(round(Decimal(value) / uniw / Decimal("1E3"), 1)) + "kuni"
    elif value < uniw * ("1E9"):
        output = str(round(Decimal(value) / uniw / Decimal("1E6"), 1)) + "Muni"
    elif value < uniw * ("1E12"):
        output = str(round(Decimal(value) / uniw / Decimal("1E9"), 1)) + "Guni"
    elif value < uniw * ("1E15"):
        output = str(round(Decimal(value) / uniw / Decimal("1E12"), 1)) + "Tuni"
    elif value < uniw * ("1E18"):
        output = str(round(Decimal(value) / uniw / Decimal("1E15"), 1)) + "Puni"
    elif value < uniw * ("1E21"):
        output = str(round(Decimal(value) / uniw / Decimal("1E18"), 1)) + "Euni"
    elif value < uniw * ("1E24"):
        output = str(round(Decimal(value) / uniw / Decimal("1E21"), 1)) + "Zuni"
    elif value < uniw * ("1E27"):
        output = str(round(Decimal(value) / uniw / Decimal("1E24"), 1)) + "Yuni"
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

# Currently unused.


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
