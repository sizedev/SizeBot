import re
import os
import io
import random
import decimal
from decimal import Decimal

import discord

import digiformatter as df
import digierror as errors
import digiSV
import userdb


# Configure decimal module.
decimal.getcontext()
context = decimal.Context(prec = 120, rounding = decimal.ROUND_HALF_EVEN,
                          Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
                          traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


# Version.
version = "3AAH.0.0.b4"

# Defaults
defaultheight = Decimal(1.754)  # meters
defaultweight = Decimal(66760)  # grams
defaultdensity = Decimal(1.0)

# Constants
newline = "\n"
folder = ".."
sizebotuser_roleid = 562356758522101769
brackets = ["[", "]", "<", ">"]
enspace = "\u2002"
printtab = enspace * 4
allowbrackets = ("&compare", "&stats")  # TODO: Could be better.

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
        return
    # Don't update owner's nick, permissions error.
    if user.id == user.guild.owner.id:
        # df.warn(f"Attempted to update user {user.id} ({user.name}), but they own this server.")
        return

    userarray = userdb.load(user.id)

    # Don't update users who aren't registered.
    if not os.path.exists(f"{folder}/users/{user.id}.txt"):
        raise errors.UserNotFoundException(user.id, userarray.nickname)

    userarray = userdb.load(user.id)

    # User's display setting is N. No sizetag.
    if userarray.display.strip() != "Y":
        return

    height = userarray.height
    if height is None:
        height = userarray.baseheight
    nick = userarray.nickname
    species = userarray.species

    unit_system = userarray.unitsystem
    if unit_system == "m":
        sizetag = digiSV.fromSV(height)
    elif unit_system == "u":
        sizetag = digiSV.fromSV(height, "u")
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
        raise errors.NoPermissions()


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
    if value > digiSV.infinity:
        return digiSV.infinity
    elif value < 0:
        return Decimal(0)
    else:
        return Decimal(value)


def changeUser(userid, changestyle, amount, attribute="height"):
    user = userdb.load(userid)
    if user is None:
        raise errors.UserNotFoundException(userid)

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
            amountSV = digiSV.toWV(getNum, getLet)
        else:
            amountSV = digiSV.toSV(getNum, getLet)

    if attribute == "height":
        if changestyle == "add":
            newamount = user.height + amountSV
        elif changestyle == "subtract":
            newamount = user.height - amountSV
        elif changestyle == "multiply":
            if value == 1:
                raise errors.ValueIsZeroException(userid, user.nickname)
            if value == 0:
                raise errors.ValueIsZeroException(userid, user.nickname)
            newamount = user.height * value
        elif changestyle == "divide":
            if value == 1:
                raise errors.ValueIsOneException(userid, user.nickname)
            if value == 0:
                raise errors.ValueIsZeroException(userid, user.nickname)
            newamount = user.height / value
        user.height = eitherInfZeroOrInput(newamount)
    else:
        raise errors.ChangeMethodInvalidException(userid, user.nickname)

    userdb.save(user)


def check(ctx):
    # Disable commands for users with the SizeBot_Banned role.
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None


df.load("Global functions loaded.")
