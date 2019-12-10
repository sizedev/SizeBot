import re
import os
import io
import math
import random
import decimal
from decimal import Decimal

import discord

import digiformatter as df
import digierror as errors


# TODO: Make this do something useful.
class DigiException(Exception):
    pass


# Configure decimal module.
decimal.getcontext()
context = decimal.Context(prec = 120, rounding = decimal.ROUND_HALF_EVEN,
                          Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
                          traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


# Version.
version = "3AAH.0.0.b3"

# Defaults
defaultheight = Decimal(1754000)  # micrometers
defaultweight = Decimal(66760000)  # milligrams
defaultdensity = Decimal(1.0)

# Constants
newline = "\n"
folder = ".."
sizebotuser_roleid = 562356758522101769
brackets = ["[", "]", "<", ">"]
enspace = "\u2002"
printtab = enspace * 4
allowbrackets = ("&compare", "&stats")  # TODO: Could be better.

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

# Slow growth tasks.
# TODO: Get rid of asyncio tasks, replace with timed database checks.
tasks = {}


def getID(*names):
    # IDs are stored in text/ids.txt.
    # The format is one ID per line, in the form {id}:{name}
    # This file is not tracked by Git.
    iddict = {}
    with io.open("text/ids.txt", "r", encoding="utf-8") as idfile:
        ids = idfile.readlines()
    ids = [x.strip() for x in ids]
    for line in ids:
        iddict[line[19:]] = line[:18].lower()
    if len(names) == 0:
        return iddict
    if len(names) == 1:
        if names in iddict.keys():
            return int(iddict[names])
        else:
            return 000000000000000000
    else:
        idlist = []
        for name in names:
            if name in iddict.keys():
                idlist.append(int(iddict[name]))
            else:
                idlist.append(000000000000000000)
        return tuple(idlist)


# Array item names.
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7


def regenHexCode():
    # 16-char hex string gen for unregister.
    hexdigits = "1234567890abcdef"
    lst = [random.choice(hexdigits) for n in range(16)]
    hexstring = "".join(lst)
    hexfile = open("text/hexstring.txt", "w")
    hexfile.write(hexstring)
    hexfile.close()


def readHexCode():
    # Read the hexcode from the file.
    hexfile = open("text/hexstring.txt", "r")
    hexcode = hexfile.readlines()
    hexfile.close()
    return str(hexcode[0])


# ASCII art.
banner = r"""
. _____ _        ______       _   _____ .
./  ___(_)       | ___ \     | | |____ |.
.\ `--. _ _______| |_/ / ___ | |_    / /.
. `--. \ |_  / _ \ ___ \/ _ \| __|   \ \.
./\__/ / |/ /  __/ |_/ / (_) | |_.___/ /.
.\____/|_/___\___\____/ \___/ \__\____/ ."""


# Get number from string.
def getNum(s):
    match = re.search(r"\d+\.?\d*", s)
    if match is None:
        return None
    return Decimal(match.group(0))


# Get letters from string.
def getLet(s):
    match = re.search(r"[a-zA-Z\'\"]+", s)
    if match is None:
        return None
    return match.group(0)


# Remove decimals.
def removeDecimals(output):
    if re.search(r"(\.\d*?)(0+)", output):
        output = re.sub(r"(\.\d*?)(0+)", r"\1", output)
    if re.search(r"(.*)(\.)(\D+)", output):
        output = re.sub(r"(.*)(\.)(\D+)", r"\1\3", output)
    return output


def removeBrackets(s):
    for bracket in brackets:
        s = s.replace(bracket, "")
    return s


def roundNearestHalf(number):
    return round(number * 2) / 2


def placeValue(number):
    return "{:,}".format(number)


# Add newlines and join into one string
def lines(items):
    return "".join(item + "\n" for item in items)


def prettyTimeDelta(seconds):
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
async def nickUpdate(user):
    if user.discriminator == "0000":
        return
    if not isinstance(user, discord.Member):
        if user.bot:
            return
        df.warn(f"Attempted to update user {user.id} ({user.name}), but they DM'd SizeBot.")
    # Don't update owner's nick, permissions error.
    if user.id == user.guild.owner.id:
        # df.warn(f"Attempted to update user {user.id} ({user.name}), but they own this server.")
        return
    # Don't update users who aren't registered.
    if not os.path.exists(f"{folder}/users/{user.id}.txt"):
        return

    userarray = readUser(user.id)

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
        df.crit(f"Tried to nickupdate {user.id} ({user.name}), but it is forbidden!")
        return


def isFeetAndInchesAndIfSoFixIt(value):
    regex = r"^(?P<feet>\d+(ft|foot|feet|\'))(?P<inch>\d+(in|\")*)"
    m = re.match(regex, value, flags=re.I)
    if not m:
        return value
    feetstr = m.group("feet")
    inchstr = m.group("inch")
    feetval = getNum(feetstr)
    inchval = getNum(inchstr)
    if feetval is None:
        feetval = 0
    if inchval is None:
        inchval = 0
    totalinches = (feetval * 12) + inchval
    return f"{totalinches}in"


def eitherInfZeroOrInput(value):
    if value > infinity:
        return infinity
    elif value < 0:
        return Decimal(0)
    else:
        return Decimal(value)


# Count users.
members = 0
path = folder + '/users'
listing = os.listdir(path)
for infile in listing:
    if infile.endswith(".txt"):
        members += 1
df.load("Loaded {0} users.".format(members))


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
def fromSV(value, accuracy=2):
    value = float(value)
    output = ""
    if value <= 0:
        return "0"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), accuracy)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), accuracy)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), accuracy)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), accuracy)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), accuracy)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), accuracy)) + "nm"
    elif value < 10**2:
        output = str(round(Decimal(value), accuracy)) + "µm"
    elif value < 10**4:
        output = str(round(Decimal(value) / Decimal(10**3), accuracy)) + "mm"
    elif value < 10**6:
        output = str(round(Decimal(value) / Decimal(10**4), accuracy)) + "cm"
    elif value < 10**9:
        output = str(round(Decimal(value) / Decimal(10**6), accuracy)) + "m"
    elif value < 10**12:
        output = str(round(Decimal(value) / Decimal(10**9), accuracy)) + "km"
    elif value < 10**15:
        output = str(round(Decimal(value) / Decimal(10**12), accuracy)) + "Mm"
    elif value < 10**18:
        output = str(round(Decimal(value) / Decimal(10**15), accuracy)) + "Gm"
    elif value < 10**21:
        output = str(round(Decimal(value) / Decimal(10**18), accuracy)) + "Tm"
    elif value < 10**24:
        output = str(round(Decimal(value) / Decimal(10**21), accuracy)) + "Pm"
    elif value < 10**27:
        output = str(round(Decimal(value) / Decimal(10**24), accuracy)) + "Em"
    elif value < 10**30:
        output = str(round(Decimal(value) / Decimal(10**27), accuracy)) + "Zm"
    elif value < uni:
        output = str(round(Decimal(value) / Decimal(10**30), accuracy)) + "Ym"
    elif value < uni * (10**3):
        output = str(round(Decimal(value) / uni, accuracy)) + "uni"
    elif value < uni * (10**6):
        output = str(round(Decimal(value) / uni / Decimal(10**3), accuracy)) + "kuni"
    elif value < uni * (10**9):
        output = str(round(Decimal(value) / uni / Decimal(10**6), accuracy)) + "Muni"
    elif value < uni * (10**12):
        output = str(round(Decimal(value) / uni / Decimal(10**9), accuracy)) + "Guni"
    elif value < uni * (10**15):
        output = str(round(Decimal(value) / uni / Decimal(10**12), accuracy)) + "Tuni"
    elif value < uni * (10**18):
        output = str(round(Decimal(value) / uni / Decimal(10**15), accuracy)) + "Puni"
    elif value < uni * (10**21):
        output = str(round(Decimal(value) / uni / Decimal(10**18), accuracy)) + "Euni"
    elif value < uni * (10**24):
        output = str(round(Decimal(value) / uni / Decimal(10**21), accuracy)) + "Zuni"
    elif value < uni * (10**27):
        output = str(round(Decimal(value) / uni / Decimal(10**24), accuracy)) + "Yuni"
    else:
        return "∞"
    return removeDecimals(output)


# Convert 'size values' to a more readable format (USA).
def fromSVUSA(value, accuracy=2):
    value = float(value)
    output = ""
    if value <= 0:
        return "0"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), accuracy)) + "ym"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), accuracy)) + "zm"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), accuracy)) + "am"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), accuracy)) + "fm"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), accuracy)) + "pm"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), accuracy)) + "nm"
    elif value < 10**2:
        output = str(round(Decimal(value), accuracy)) + "µm"
    elif value < 10**4:
        output = str(round(Decimal(value) / Decimal(10**3), accuracy)) + "mm"
    elif value < foot:
        output = str(round(Decimal(value) / inch, accuracy)) + "in"
    elif value < mile:
        feetval = math.floor(Decimal(value) / foot)
        fulloninches = round(Decimal(value) / inch, accuracy)
        feettoinches = feetval * Decimal(12)
        inchval = fulloninches - feettoinches
        output = str(feetval) + "'" + str(inchval) + "\""
    elif value < au:
        output = str(round(Decimal(value) / mile, accuracy)) + "mi"
    elif value < ly:
        output = str(round(Decimal(value) / au, accuracy)) + "AU"
    elif value < uni / 10:
        output = str(round(Decimal(value) / ly, accuracy)) + "ly"
    elif value < uni * (10**3):
        output = str(round(Decimal(value) / uni, accuracy)) + "uni"
    elif value < uni * (10**6):
        output = str(round(Decimal(value) / uni / Decimal(10**3), accuracy)) + "kuni"
    elif value < uni * (10**9):
        output = str(round(Decimal(value) / uni / Decimal(10**6), accuracy)) + "Muni"
    elif value < uni * (10**12):
        output = str(round(Decimal(value) / uni / Decimal(10**9), accuracy)) + "Guni"
    elif value < uni * (10**15):
        output = str(round(Decimal(value) / uni / Decimal(10**12), accuracy)) + "Tuni"
    elif value < uni * (10**18):
        output = str(round(Decimal(value) / uni / Decimal(10**15), accuracy)) + "Puni"
    elif value < uni * (10**21):
        output = str(round(Decimal(value) / uni / Decimal(10**18), accuracy)) + "Euni"
    elif value < uni * (10**24):
        output = str(round(Decimal(value) / uni / Decimal(10**21), accuracy)) + "Zuni"
    elif value < uni * (10**27):
        output = str(round(Decimal(value) / uni / Decimal(10**24), accuracy)) + "Yuni"
    else:
        return "∞"
    return removeDecimals(output)


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
def fromWV(value, accuracy=2):
    value = Decimal(value)
    if value <= 0:
        return "0"
    elif value < 0.000000000000000001:
        output = str(round(Decimal(value) * Decimal(10**21), accuracy)) + "yg"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), accuracy)) + "zg"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), accuracy)) + "ag"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), accuracy)) + "fg"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), accuracy)) + "pg"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), accuracy)) + "ng"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), accuracy)) + "µg"
    elif value < 1000:
        output = str(round(Decimal(value), accuracy)) + "mg"
    elif value < 10000000:
        output = str(round(Decimal(value) / Decimal(10**3), accuracy)) + "g"
    elif value < 1000000000:
        output = str(round(Decimal(value) / Decimal(10**6), accuracy)) + "kg"
    elif value < 100000000000:
        output = str(round(Decimal(value) / Decimal(10**9), accuracy)) + "t"
    elif value < 100000000000000:
        output = str(round(Decimal(value) / Decimal(10**12), accuracy)) + "kt"
    elif value < 100000000000000000:
        output = str(round(Decimal(value) / Decimal(10**15), accuracy)) + "Mt"
    elif value < 100000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**18), accuracy)) + "Gt"
    elif value < 100000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**21), accuracy)) + "Tt"
    elif value < 100000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**24), accuracy)) + "Pt"
    elif value < 100000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**27), accuracy)) + "Et"
    elif value < 100000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**30), accuracy)) + "Zt"
    elif value < 100000000000000000000000000000000000:
        output = str(round(Decimal(value) / Decimal(10**33), accuracy)) + "Yt"
    elif value < uniw * (10**3):
        output = str(round(Decimal(value) / uniw, accuracy)) + "uni"
    elif value < uniw * (10**6):
        output = str(round(Decimal(value) / uniw / Decimal(10**3), accuracy)) + "kuni"
    elif value < uniw * (10**9):
        output = str(round(Decimal(value) / uniw / Decimal(10**6), accuracy)) + "Muni"
    elif value < uniw * (10**12):
        output = str(round(Decimal(value) / uniw / Decimal(10**9), accuracy)) + "Guni"
    elif value < uniw * (10**15):
        output = str(round(Decimal(value) / uniw / Decimal(10**12), accuracy)) + "Tuni"
    elif value < uniw * (10**18):
        output = str(round(Decimal(value) / uniw / Decimal(10**15), accuracy)) + "Puni"
    elif value < uniw * (10**21):
        output = str(round(Decimal(value) / uniw / Decimal(10**18), accuracy)) + "Euni"
    elif value < uniw * (10**24):
        output = str(round(Decimal(value) / uniw / Decimal(10**21), accuracy)) + "Zuni"
    elif value < uniw * (10**27):
        output = str(round(Decimal(value) / uniw / Decimal(10**24), accuracy)) + "Yuni"
    else:
        return "∞"
    return removeDecimals(output)


# Convert 'weight values' to a more readable format (USA).
def fromWVUSA(value, accuracy=2):
    value = Decimal(value)
    if value == 0:
        return "almost nothing"
    elif value < 0.000000000000000001:
        output = str(round(Decimal(value) * Decimal(10**21), accuracy)) + "yg"
    elif value < 0.000000000000001:
        output = str(round(Decimal(value) * Decimal(10**18), accuracy)) + "zg"
    elif value < 0.000000000001:
        output = str(round(Decimal(value) * Decimal(10**15), accuracy)) + "ag"
    elif value < 0.000000001:
        output = str(round(Decimal(value) * Decimal(10**12), accuracy)) + "fg"
    elif value < 0.000001:
        output = str(round(Decimal(value) * Decimal(10**9), accuracy)) + "pg"
    elif value < 0.001:
        output = str(round(Decimal(value) * Decimal(10**6), accuracy)) + "ng"
    elif value < 1:
        output = str(round(Decimal(value) * Decimal(10**3), accuracy)) + "µg"
    elif value < 1000:
        output = str(round(Decimal(value), accuracy)) + "mg"
    elif value < (ounce / 10):
        output = str(round(Decimal(value) / Decimal(10**3), accuracy)) + "g"
    elif value < pound:
        output = str(placeValue(round(Decimal(value) / ounce, accuracy))) + "oz"
    elif value < uston:
        output = str(placeValue(round(Decimal(value) / pound, accuracy))) + "lb"
    elif value < earth / 10:
        output = str(placeValue(round(Decimal(value) / uston, accuracy))) + " US tons"
    elif value < sun / 10:
        output = str(placeValue(round(Decimal(value) / earth, accuracy))) + " Earths"
    elif value < milkyway:
        output = str(placeValue(round(Decimal(value) / sun, accuracy))) + " Suns"
    elif value < uniw:
        output = str(placeValue(round(Decimal(value) / milkyway, accuracy))) + " Milky Ways"
    elif value < uniw * (10**3):
        output = str(round(Decimal(value) / uniw, accuracy)) + "uni"
    elif value < uniw * (10**6):
        output = str(round(Decimal(value) / uniw / Decimal(10**3), accuracy)) + "kuni"
    elif value < uniw * (10**9):
        output = str(round(Decimal(value) / uniw / Decimal(10**6), accuracy)) + "Muni"
    elif value < uniw * (10**12):
        output = str(round(Decimal(value) / uniw / Decimal(10**9), accuracy)) + "Guni"
    elif value < uniw * (10**15):
        output = str(round(Decimal(value) / uniw / Decimal(10**12), accuracy)) + "Tuni"
    elif value < uniw * (10**18):
        output = str(round(Decimal(value) / uniw / Decimal(10**15), accuracy)) + "Puni"
    elif value < uniw * (10**21):
        output = str(round(Decimal(value) / uniw / Decimal(10**18), accuracy)) + "Euni"
    elif value < uniw * (10**24):
        output = str(round(Decimal(value) / uniw / Decimal(10**21), accuracy)) + "Zuni"
    elif value < uniw * (10**27):
        output = str(round(Decimal(value) / uniw / Decimal(10**24), accuracy)) + "Yuni"
    else:
        return "∞"
    return removeDecimals(output)


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
    shoesize = placeValue(roundNearestHalf(shoesize))
    if child:
        shoesize = "Children's " + shoesize
    return "Size US " + shoesize


# Currently unused.
def fromShoeSize(size):
    child = False
    if "c" in size.toLower():
        child = True
    size = getNum(size)
    inches = Decimal(size) + 22
    if child:
        inches = Decimal(size) + 22 - 12 - (1 / 3)
    inches = inches / Decimal(3)
    out = inches * inch
    return out


# Read in specific user.
# TODO: Read this from a MariaDB. Rewrite like all of this.
def readUser(user_id):
    user_id = str(user_id)
    userfile = folder + "/users/" + user_id + ".txt"
    if not os.path.isfile(userfile):
        return None
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
        content[CHEI] = round(float(content[CHEI]), 18)
        content[BHEI] = round(float(content[BHEI]), 18)
        content[BWEI] = round(float(content[BWEI]), 18)

        content = [item.strip() for item in content]

        for idx, item in enumerate(content):
            if idx in [CHEI, BHEI, BWEI, DENS]:
                content[idx] = Decimal(item)

        return content


# Write to specific user.
# TODO: Read this from a MariaDB. Rewrite like all of this.
def writeUser(user_id, content):
    user_id = str(user_id)
    # Replace None.
    if content[BWEI] == "None" + newline:
        content[BWEI] = str(defaultweight) + newline
    if content[BHEI] == "None" + newline:
        content[BHEI] = str(defaultheight) + newline
    if content[CHEI] == "None" + newline:
        content[CHEI] = content[3]
    # Round all values to 18 decimal places.
    content[CHEI] = str(round(float(content[CHEI]), 18))
    content[BHEI] = str(round(float(content[BHEI]), 18))
    content[BWEI] = str(round(float(content[BWEI]), 18))
    # Add new line characters to entries that don't have them.
    for idx, item in enumerate(content):
        item = str(item)
        if not item.endswith("\n"):
            item = item + "\n"
        context[idx] = item
    # Delete userfile.
    os.remove(folder + "/users/" + user_id + ".txt")
    # Make a new userfile.
    userfile = open(folder + "/users/" + user_id + ".txt", "w+")
    # Write content to lines.
    userfile.writelines(content)


def changeUser(userid, changestyle, amount, attribute="height"):
    user = readUser(userid)
    if user is None:
        return errors.USER_NOT_FOUND

    changestyle = changestyle.lower()
    if changestyle in ["add", "+", "a", "plus"]:
        changestyle = "add"
    if changestyle in ["subtract", "sub", "-", "minus"]:
        changestyle = "subtract"
    if changestyle in ["multiply", "mult", "m", "x", "times"]:
        changestyle = "multiply"
    if changestyle in ["divide", "d", "/", "div"]:
        changestyle = "divide"

    amount = isFeetAndInchesAndIfSoFixIt(amount)
    value = getNum(amount)
    unit = getLet(amount)
    amountSV = 0
    if unit:
        if attribute == "weight":
            amountSV = toWV(getNum, getLet)
        else:
            amountSV = toSV(getNum, getLet)

    if attribute == "height":
        if changestyle == "add":
            newamount = user[CHEI] + amountSV
        elif changestyle == "subtract":
            newamount = user[CHEI] - amountSV
        elif changestyle == "multiply":
            if value == 1:
                return errors.CHANGE_VALUE_IS_ONE
            if value == 0:
                return errors.CHANGE_VALUE_IS_ZERO
            newamount = user[CHEI] * value
        elif changestyle == "divide":
            if value == 1:
                return errors.CHANGE_VALUE_IS_ONE
            if value == 0:
                return errors.CHANGE_VALUE_IS_ZERO
            newamount = user[CHEI] / value
        user[CHEI] = eitherInfZeroOrInput(newamount)
    else:
        return errors.CHANGE_METHOD_INVALID

    writeUser(userid, user)
    return errors.SUCCESS


def check(ctx):
    # Disable commands for users with the SizeBot_Banned role.
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None


df.load("Global functions loaded.")
