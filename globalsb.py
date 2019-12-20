import decimal

import discord

import digiformatter as df
import digierror as errors
import digiSV
import userdb
import utils


# Configure decimal module.
decimal.getcontext()
context = decimal.Context(prec = 120, rounding = decimal.ROUND_HALF_EVEN,
                          Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
                          traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


# Slow growth tasks.
# TODO: Get rid of asyncio tasks, replace with timed database checks.
tasks = {}


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
        raise errors.NoPermissionsException


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

    userdata.height = utils.clamp(0, newamount, digiSV.infinity)

    userdb.save(userdata)


df.load("Global functions loaded.")
