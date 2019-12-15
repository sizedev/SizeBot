import re
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

# Constants
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


def removeBrackets(s):
    for bracket in brackets:
        s = s.replace(bracket, "")
    return s


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
        return
    if user.bot:
        return
    # Don't update owner's nick, permissions error.
    if user.id == user.guild.owner.id:
        # df.warn(f"Attempted to update user {user.id} ({user.name}), but they own this server.")
        return

    userdata = userdb.load(user.id)

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    height = userdata.height
    if height is None:
        height = userdata.baseheight
    nick = userdata.nickname
    species = userdata.species

    if userdata.unitsystem in ["m", "u"]:
        sizetag = digiSV.fromSV(height, userdata.unitsystem)
    else:
        sizetag = ""

    if species is not None:
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


def clamp(minVal, val, maxVal):
    return max(minVal, min(maxVal, val))


def changeUser(userid, changestyle, amount):
    changestyle = changestyle.lower()
    if changestyle in ["add", "+", "a", "plus"]:
        changestyle = "add"
    if changestyle in ["subtract", "sub", "-", "minus"]:
        changestyle = "subtract"
    if changestyle in ["multiply", "mult", "m", "x", "times"]:
        changestyle = "multiply"
    if changestyle in ["divide", "d", "/", "div"]:
        changestyle = "divide"

    if changestyle not in ["add", "subtract", "multiply", "divide"]:
        return
        # TODO: raise an error

    if changestyle in ["add", "subtract"]:
        amountSV = digiSV.toSV(amount)
    elif changestyle in ["multiply", "divide"]:
        amountVal = digiSV.getNum(amount)
        if amountVal == 1:
            raise errors.ValueIsOneException
        if amountVal == 0:
            raise errors.ValueIsZeroException

    userdata = userdb.load(userid)

    if changestyle == "add":
        newamount = userdata.height + amountSV
    elif changestyle == "subtract":
        newamount = userdata.height - amountSV
    elif changestyle == "multiply":
        newamount = userdata.height * amountVal
    elif changestyle == "divide":
        newamount = userdata.height / amountVal

    userdata.height = clamp(0, newamount, digiSV.infinity)

    userdb.save(userdata)


def check(ctx):
    # Disable commands for users with the SizeBot_Banned role.
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None


df.load("Global functions loaded.")
