from copy import copy
import math
import re

import discord
from discord import Embed

from sizebot import __version__
from sizebot.lib import errors, macrovision, userdb, utils
from sizebot.lib.constants import colors, emojis
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import defaultheight, defaultweight, defaultterminalvelocity, defaultliftstrength, falllimit
from sizebot.lib.utils import prettyTimeDelta, url_safe


compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"


# TODO: Move to somewhere other than here.
# Update users nicknames to include sizetags
async def nickUpdate(user):
    # webhooks
    if user.discriminator == "0000":
        return
    # non-guild messages
    if not isinstance(user, discord.Member):
        return
    # bots
    if user.bot:
        return
    # guild owner
    if user.id == user.guild.owner_id:
        return

    try:
        userdata = userdb.load(user.guild.id, user.id)
    except errors.UserNotFoundException:
        return

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    height = userdata.height
    if height is None:
        height = userdata.baseheight
    nick = userdata.nickname
    species = userdata.species

    if userdata.unitsystem in ["m", "u", "o"]:
        sizetag = format(height, f",{userdata.unitsystem}%")
    else:
        sizetag = ""

    if species is not None:
        sizetag = f"{sizetag}, {species}"

    max_nick_len = 32

    if len(nick) > max_nick_len:
        # Truncate nick is too long
        nick = nick[:max_nick_len]

    if len(nick) + len(sizetag) + 3 <= max_nick_len:
        # Fit full nick and sizetag
        newnick = f"{nick} [{sizetag}]"
    elif len(sizetag) + 7 <= max_nick_len:
        # Fit short nick and sizetag
        chars_left = max_nick_len - len(sizetag) - 4
        short_nick = nick[:chars_left]
        newnick = f"{short_nick}… [{sizetag}]"
    else:
        # Cannot fit the new sizetag
        newnick = nick
    try:
        await user.edit(nick = newnick)
    except discord.Forbidden:
        raise errors.NoPermissionsException


# TODO: Move to somewhere other than here.
async def nickReset(user):
    """Remove sizetag from user's nickname"""
    # webhooks
    if user.discriminator == "0000":
        return
    # non-guild messages
    if not isinstance(user, discord.Member):
        return
    # bots
    if user.bot:
        return
    # guild owner
    if user.id == user.guild.owner_id:
        return

    userdata = userdb.load(user.guild.id, user.id, allow_unreg=True)

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    try:
        await user.edit(nick = userdata.nickname)
    except discord.Forbidden:
        raise errors.NoPermissionsException


def changeUser(guildid, userid, changestyle, amount):
    changestyle = changestyle.lower()
    if changestyle in ["add", "+", "a", "plus"]:
        changestyle = "add"
    if changestyle in ["subtract", "sub", "-", "minus"]:
        changestyle = "subtract"
    if changestyle in ["power", "exp", "pow", "exponent", "^", "**"]:
        changestyle = "power"
    if changestyle in ["multiply", "mult", "m", "x", "times", "*"]:
        changestyle = "multiply"
    if changestyle in ["divide", "d", "/", "div"]:
        changestyle = "divide"
    if changestyle in ["percent", "per", "perc", "%"]:
        changestyle = "percent"

    if changestyle not in ["add", "subtract", "multiply", "divide", "power", "percent"]:
        raise errors.ChangeMethodInvalidException(changestyle)

    amountSV = None
    amountVal = None
    newamount = None

    if changestyle in ["add", "subtract"]:
        amountSV = SV.parse(amount)
    elif changestyle in ["multiply", "divide", "power"]:
        amountVal = Decimal(amount)
        if amountVal == 1:
            raise errors.ValueIsOneException
        if amountVal == 0:
            raise errors.ValueIsZeroException
    elif changestyle in ["percent"]:
        amountVal = Decimal(amount)
        if amountVal == 0:
            raise errors.ValueIsZeroException

    userdata = userdb.load(guildid, userid)

    if changestyle == "add":
        newamount = userdata.height + amountSV
    elif changestyle == "subtract":
        newamount = userdata.height - amountSV
    elif changestyle == "multiply":
        newamount = userdata.height * amountVal
    elif changestyle == "divide":
        newamount = userdata.height / amountVal
    elif changestyle == "power":
        userdata = userdata ** amountVal
    elif changestyle == "percent":
        newamount = userdata.height * (amountVal / 100)

    if changestyle != "power":
        userdata.height = newamount

    userdb.save(userdata)


class PersonComparison:  # TODO: Make a one-sided comparison option.
    def __init__(self, userdata1, userdata2):
        smallUserdata, bigUserdata = utils.minmax(userdata1, userdata2)
        self.big = PersonStats(bigUserdata)
        self.small = PersonStats(smallUserdata)

        bigToSmallUserdata = copy(bigUserdata)
        smallToBigUserdata = copy(smallUserdata)

        if bigUserdata.height == 0 and smallUserdata.height == 0:
            self.multiplier = Decimal(1)
        else:
            self.multiplier = bigUserdata.height / smallUserdata.height
            bigToSmallUserdata.height = bigUserdata.height * smallUserdata.viewscale
            smallToBigUserdata.height = smallUserdata.height * bigUserdata.viewscale

        self.bigToSmall = PersonStats(bigToSmallUserdata)
        self.smallToBig = PersonStats(smallToBigUserdata)

        self.footlabel = "Foot/Paw" if bigUserdata.pawtoggle or smallUserdata.pawtoggle else "Foot"
        self.hairlabel = "Hair/Fur" if bigUserdata.furtoggle or smallUserdata.furtoggle else "Hair"

        viewangle = calcViewAngle(smallUserdata.height, bigUserdata.height)
        self.lookangle = abs(viewangle)
        self.lookdirection = "up" if viewangle >= 0 else "down"

    def __str__(self):
        return f"<PersonComparison SMALL = {self.small!r}, BIG = {self.big!r}, SMALLTOBIG = {self.smallToBig!r}, BIGTOSMALL = {self.bigToSmall!r}>"

    def __repr__(self):
        return str(self)

    async def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(
            title=f"Comparison of {self.big.nickname} and {self.small.nickname} 🔗",
            description=f"*Requested by {requestertag}*",
            color=colors.purple,
            url = await self.url()
        )
        if requestertag == self.big.tag:
            embed.color = colors.blue
        if requestertag == self.small.tag:
            embed.color = colors.red
        embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
        embed.add_field(name=f"{emojis.comparebigcenter} **{self.big.nickname}**", value=(
            f"{emojis.blank}{emojis.blank} **Height:** {self.big.height:,.3mu}\n"
            f"{emojis.blank}{emojis.blank} **Weight:** {self.big.weight:,.3mu}\n"), inline=True)
        embed.add_field(name=f"{emojis.comparesmallcenter} **{self.small.nickname}**", value=(
            f"{emojis.blank}{emojis.blank} **Height:** {self.small.height:,.3mu}\n"
            f"{emojis.blank}{emojis.blank} **Weight:** {self.small.weight:,.3mu}\n"), inline=True)
        embed.add_field(value=(
            f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{self.big.nickname}** looks to {emojis.comparesmallcenter} **{self.small.nickname}**.\n"
            f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{self.small.nickname}** looks to {emojis.comparebigcenter} **{self.big.nickname}**."), inline=False)
        embed.add_field(name="Height", value=(
            f"{emojis.comparebig}{self.bigToSmall.height:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.height:,.3mu}"), inline=True)
        embed.add_field(name="Weight", value=(
            f"{emojis.comparebig}{self.bigToSmall.weight:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.weight:,.3mu}"), inline=True)
        embed.add_field(name=f"{self.footlabel} Length", value=(
            f"{emojis.comparebig}{self.bigToSmall.footlength:,.3mu} ({self.bigToSmall.shoesize})\n"
            f"{emojis.comparesmall}{self.smallToBig.footlength:,.3mu} ({self.smallToBig.shoesize})"), inline=True)
        embed.add_field(name=f"{self.footlabel} Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.footwidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.footwidth:,.3mu}"), inline=True)
        embed.add_field(name="Toe Height", value=(
            f"{emojis.comparebig}{self.bigToSmall.toeheight:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.toeheight:,.3mu}"), inline=True)
        embed.add_field(name="Shoeprint Depth", value=(
            f"{emojis.comparebig}{self.bigToSmall.shoeprintdepth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.shoeprintdepth:,.3mu}"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=(
            f"{emojis.comparebig}{self.bigToSmall.pointerlength:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.pointerlength:,.3mu}"), inline=True)
        embed.add_field(name="Thumb Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.thumbwidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.thumbwidth:,.3mu}"), inline=True)
        embed.add_field(name="Nail Thickness", value=(
            f"{emojis.comparebig}{self.bigToSmall.nailthickness:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.nailthickness:,.3mu}"), inline=True)
        embed.add_field(name="Fingerprint Depth", value=(
            f"{emojis.comparebig}{self.bigToSmall.fingerprintdepth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.fingerprintdepth:,.3mu}"), inline=True)
        if self.bigToSmall.hairlength or self.smallToBig.hairlength:
            hairfield = ""
            if self.bigToSmall.hairlength:
                hairfield += f"{emojis.comparebig}{self.bigToSmall.hairlength:,.3mu}\n"
            if self.smallToBig.hairlength:
                hairfield += f"{emojis.comparebig}{self.smallToBig.hairlength:,.3mu}\n"
            hairfield = hairfield.strip()
            embed.add_field(name=f"{self.hairlabel} Length", value=hairfield, inline=True)
        if self.bigToSmall.taillength or self.smallToBig.taillength:
            tailfield = ""
            if self.bigToSmall.taillength:
                tailfield += f"{emojis.comparebig}{self.bigToSmall.taillength:,.3mu}\n"
            if self.smallToBig.taillength:
                tailfield += f"{emojis.comparebig}{self.smallToBig.taillength:,.3mu}\n"
            tailfield = tailfield.strip()
            embed.add_field(name="Tail Length", value=tailfield, inline=True)
        if self.bigToSmall.earheight or self.smallToBig.earheight:
            earfield = ""
            if self.bigToSmall.earheight:
                earfield += f"{emojis.comparebig}{self.bigToSmall.earheight:,.3mu}\n"
            if self.smallToBig.earheight:
                earfield += f"{emojis.comparebig}{self.smallToBig.earheight:,.3mu}\n"
            earfield = earfield.strip()
            embed.add_field(name="Ear Height", value=earfield, inline=True)
        embed.add_field(name=f"{self.hairlabel} Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.hairwidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.hairwidth:,.3mu}"), inline=True)
        embed.add_field(name="Eye Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.eyewidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.eyewidth:,.3mu}"), inline=True)
        embed.add_field(name="Walk Speed", value=(
            f"{emojis.comparebig}{self.bigToSmall.walkperhour:,.1M} per hour ({self.bigToSmall.walkperhour:,.1U} per hour)\n"
            f"{emojis.comparesmall}{self.smallToBig.walkperhour:,.1M} per hour ({self.smallToBig.walkperhour:,.1U} per hour)"), inline=True)
        embed.add_field(name="Run Speed", value=(
            f"{emojis.comparebig}{self.bigToSmall.runperhour:,.1M} per hour ({self.bigToSmall.runperhour:,.1U} per hour)\n"
            f"{emojis.comparesmall}{self.smallToBig.runperhour:,.1M} per hour ({self.smallToBig.runperhour:,.1U} per hour)"), inline=True)
        embed.add_field(name="Lift/Carry Strength", value=(
            f"{emojis.comparebig}{self.bigToSmall.liftstrength:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.liftstrength:,.3mu}"), inline=True)
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}."))
        return embed

    async def url(self):
        safeSmallNick = url_safe(self.small.nickname)
        safeBigNick = url_safe(self.big.nickname)

        compUrl = await macrovision.get_url([
            {
                "name": safeSmallNick,
                "model": self.small.macrovision_model,
                "view": self.small.macrovision_view,
                "height": self.small.height
            },
            {
                "name": safeBigNick,
                "model": self.big.macrovision_model,
                "view": self.big.macrovision_view,
                "height": self.big.height
            }
        ])
        return compUrl


class PersonSpeedComparison:
    def __init__(self, userdata1, userdata2):
        self.viewer = PersonStats(userdata1)
        self.viewed = PersonStats(userdata2)

        self.viewertovieweddata = copy(userdata1)
        self.viewedtoviewerdata = copy(userdata2)

        if self.viewer.height == 0 and self.viewed.height == 0:
            self.multiplier = Decimal(1)
        else:
            self.multiplier = self.viewed.height / self.viewer.height

        self.viewedtoviewer = PersonStats(self.viewedtoviewerdata)
        self.viewertoviewed = PersonStats(self.viewertovieweddata)

        self.footlabel = "Foot/Paw" if self.viewed.pawtoggle else "Foot"
        self.hairlabel = "Hair/Fur" if self.viewed.furtoggle else "Hair"

        viewangle = calcViewAngle(self.viewer.height, self.viewed.height)
        self.lookangle = abs(viewangle)
        self.lookdirection = "up" if viewangle >= 0 else "down"

    def __str__(self):
        return f"<PersonSpeedComparison VIEWER = {self.viewer!r}, VIEWED = {self.viewed!r}, \
            VIEWERTOVIEWED = {self.viewertoviewed!r}, VIEWEDTOVIEWER = {self.viewedtoviewer!r}>"

    def __repr__(self):
        return str(self)

    def speedcalc(self, dist: SV):
        climblength = Decimal(0.3048) / self.viewer.viewscale
        climbspeed = Decimal(4828) / self.viewer.viewscale

        _walktime = (dist / self.viewer.walkperhour) * 60 * 60
        walksteps = math.ceil(dist / self.viewer.walksteplength)
        _runtime = (dist / self.viewer.runperhour) * 60 * 60
        runsteps = math.ceil(dist / self.viewer.runsteplength)
        _climbtime = (dist / climbspeed) * 60 * 60
        climbsteps = math.ceil(dist / climblength)
        walktime = prettyTimeDelta(_walktime)
        runtime = prettyTimeDelta(_runtime)
        climbtime = prettyTimeDelta(_climbtime)

        return (
            f"{emojis.ruler} {dist:,.3mu}\n"
            f"{emojis.walk} {walktime} ({walksteps:,.3} steps)\n"
            f"{emojis.run} {runtime} ({runsteps:,.3} steps)\n"
            f"{emojis.climb} {climbtime} ({climbsteps:,.3} pulls)"
        )

    async def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(
            title=f"Speed/Distance Comparison of {self.viewed.nickname} and {self.viewer.nickname}",
            description=f"*Requested by {requestertag}*",
            color=colors.purple
        )
        embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
        embed.add_field(name=f"**{self.viewer.nickname}** Speeds", value=(
            f"{emojis.blank} **Walk Speed:** {self.viewer.walkperhour:,.3mu} per hour\n"
            f"{emojis.blank} **Run Speed:** {self.viewer.runperhour:,.3mu} per hour"), inline=False)
        embed.add_field(name="Height", value=(self.speedcalc(self.viewedtoviewer.height)), inline=True)
        embed.add_field(name=f"{self.footlabel} Length", value=(self.speedcalc(self.viewedtoviewer.footlength)), inline=True)
        embed.add_field(name=f"{self.footlabel} Width", value=(self.speedcalc(self.viewedtoviewer.footwidth)), inline=True)
        embed.add_field(name="Toe Height", value=(self.speedcalc(self.viewedtoviewer.toeheight)), inline=True)
        embed.add_field(name="Shoeprint Depth", value=(self.speedcalc(self.viewedtoviewer.shoeprintdepth)), inline=True)
        embed.add_field(name="Pointer Finger Length", value=(self.speedcalc(self.viewedtoviewer.pointerlength)), inline=True)
        embed.add_field(name="Thumb Width", value=(self.speedcalc(self.viewedtoviewer.thumbwidth)), inline=True)
        embed.add_field(name="Nail Thickness", value=(self.speedcalc(self.viewedtoviewer.nailthickness)), inline=True)
        embed.add_field(name="Fingerprint Depth", value=(self.speedcalc(self.viewedtoviewer.fingerprintdepth)), inline=True)
        if self.viewedtoviewer.hairlength:
            embed.add_field(name=f"{self.hairlabel} Length", value=(self.speedcalc(self.viewedtoviewer.hairlength)), inline=True)
        if self.viewedtoviewer.taillength:
            embed.add_field(name=f"Tail Length", value=(self.speedcalc(self.viewedtoviewer.taillength)), inline=True)
        if self.viewedtoviewer.earheight:
            embed.add_field(name=f"Ear Height", value=(self.speedcalc(self.viewedtoviewer.earheight)), inline=True)
        embed.add_field(name=f"{self.hairlabel} Width", value=(self.speedcalc(self.viewedtoviewer.hairwidth)), inline=True)
        embed.add_field(name="Eye Width", value=(self.speedcalc(self.viewedtoviewer.eyewidth)), inline=True)
        embed.set_footer(text=(f"{self.viewed.nickname} is {self.multiplier:,.3}x taller than {self.viewer.nickname}."))
        return embed


class PersonStats:
    # Conversion constants
    footfactor = 1 / Decimal("7")
    footwidthfactor = footfactor / Decimal("2.5")
    toeheightfactor = 1 / Decimal("65")
    thumbfactor = 1 / Decimal("69.06")
    fingerprintfactor = 1 / Decimal("35080")
    hairfactor = 1 / Decimal("23387")
    pointerfactor = 1 / Decimal("17.26")
    nailthickfactor = 1 / Decimal("2920")
    shoeprintfactor = 1 / Decimal("135")
    eyewidthfactor = 1 / Decimal("73.083")

    walkstepsperhour = 6900
    runstepsperhour = 10200

    defaultthreadthickness = Decimal("0.001016")

    defaultwalkspeed = 5630
    defaultrunspeed = 12100

    def __init__(self, userdata):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.gender = userdata.autogender
        self.height = userdata.height
        self.baseheight = userdata.baseheight
        self.viewscale = userdata.viewscale
        self.scale = userdata.scale
        self.formattedscale = userdata.getFormattedScale(verbose = True)
        self.baseweight = userdata.baseweight
        self.weight = userdata.weight
        self.formattedweightscale = userdata.getFormattedScale(scaletype = "weight", verbose = True)
        self.footname = userdata.footname
        self.hairname = userdata.hairname
        self.pawtoggle = userdata.pawtoggle
        self.furtoggle = userdata.furtoggle
        self.macrovision_model = userdata.macrovision_model
        self.macrovision_view = userdata.macrovision_view

        self.averageheightmult = self.height / defaultheight
        self.averageweightmult = self.weight / defaultweight

        if userdata.hairlength is None:
            self.hairlength = None
        else:
            self.hairlength = SV(userdata.hairlength / self.viewscale)

        if userdata.taillength is None:
            self.taillength = None
        else:
            self.taillength = SV(userdata.taillength / self.viewscale)

        if userdata.earheight is None:
            self.earheight = None
        else:
            self.earheight = SV(userdata.earheight / self.viewscale)

        if userdata.liftstrength is None:
            self.liftstrength = WV(defaultliftstrength / (self.viewscale ** 3))
        else:
            self.liftstrength = WV(userdata.liftstrength / (self.viewscale ** 3))

        if userdata.footlength is None:
            self.footlength = SV(self.height * self.footfactor)
        else:
            self.footlength = SV(userdata.footlength / self.viewscale)
        self.shoesize = formatShoeSize(self.footlength, self.gender == "f")
        self.footwidth = SV(self.height * self.footwidthfactor)
        self.toeheight = SV(self.height * self.toeheightfactor)
        self.shoeprintdepth = SV(self.height * self.toeheightfactor)
        self.pointerlength = SV(self.height * self.pointerfactor)
        self.thumbwidth = SV(self.height * self.thumbfactor)
        self.fingerprintdepth = SV(self.height * self.fingerprintfactor)

        self.threadthickness = SV(self.defaultthreadthickness * self.averageheightmult)

        self.hairwidth = SV(self.height * self.hairfactor)
        self.nailthickness = SV(self.height * self.nailthickfactor)
        self.eyewidth = SV(self.height * self.eyewidthfactor)

        self.avgheightcomp = SV(defaultheight * self.viewscale)
        self.avgweightcomp = WV(defaultweight * self.viewscale ** 3)

        viewangle = calcViewAngle(self.height, defaultheight)
        self.avglookangle = abs(viewangle)
        self.avglookdirection = "up" if viewangle >= 0 else "down"

        if userdata.walkperhour is None:
            self.walkperhour = SV(self.defaultwalkspeed * self.averageheightmult)
        else:
            self.walkperhour = SV(userdata.walkperhour * self.averageheightmult)

        if userdata.runperhour is None:
            self.runperhour = SV(self.defaultrunspeed * self.averageheightmult)
        else:
            self.runperhour = SV(userdata.runperhour * self.averageheightmult)

        self.walksteplength = SV(self.walkperhour / self.walkstepsperhour)
        self.runsteplength = SV(self.runperhour / self.runstepsperhour)

        self.horizondistance = SV(math.sqrt(math.pow(self.height + 6378137, 2) - 40680631590769))

        self.terminalvelocity = SV(defaultterminalvelocity * Decimal(math.sqrt(self.scale)))
        self.fallproof = self.terminalvelocity < falllimit
        self.fallproofcheck = emojis.voteyes if self.fallproof else emojis.voteno

    def getFormattedStat(self, stat):
        returndict = {
            "height": f"'s current height is **{self.height:,.3mu}**, or {self.formattedscale} scale.",
            "weight": f"'s current weight is **{self.weight:,.3mu}**.",
            "foot": f"'s {self.footname.lower()} is **{self.footlength:,.3mu}** long and **{self.footwidth:,.3mu}** wide. ({self.shoesize})",
            "toe": f"'s toe is **{self.toeheight:,.3mu}** thick.",
            "shoeprint": f"'s shoe print is **{self.shoeprintdepth:,.3mu}** deep.",
            "finger": f"'s pointer finger is **{self.pointerlength:,.3mu}** long.",
            "thumb": f"'s thumb is **{self.thumbwidth:,.3mu}** wide.",
            "nail": f"'s nail is **{self.nailthickness:,.3mu}** thick.",
            "fingerprint": f"'s fingerprint is **{self.fingerprintdepth:,.3mu}** deep.",
            "thread": f"'s clothing threads are **{self.threadthickness:,.3mu}** thick.",
            "eye": f"'s eye is **{self.eyewidth:,.3mu}** wide.",
            "speed": f" walks at **{self.walkperhour:,.1M} per hour** ({self.walkperhour:,.1U} per hour), with {self.walksteplength:,.1m}/{self.walksteplength:,.1u} strides, and runs at **{self.runperhour:,.1M} per hour** ({self.runperhour:,.1U} per hour), with {self.runsteplength:,.1m}/{self.runsteplength:,.1u} strides.",
            "base": f" is **{self.baseheight:,.3mu}** tall and weigh **{self.baseweight:,.3mu}** at their base size.",
            "compare": f" sees an average person as being **{self.avgheightcomp:,.3mu}** and weighing **{self.avgweightcomp:,.3mu}**.",
            "scale": f" is **{self.formattedscale}** their base height.",
            "horizondistance": f" can see for **{self.horizondistance:,.3mu}** to the horizon.",
            "liftstrength": f"can lift and carry **{self.liftstrength}."
        }
        if self.hairlength:
            returndict["hair"] = f"'s {self.hairname.lower()} is **{self.hairlength:,.3mu}** long."
        if self.taillength:
            returndict["tail"] = f"'s tail is **{self.taillength:,.3mu}** long."
        if self.earheight:
            returndict["ear"] = f"'s tail is **{self.earheight:,.3mu}** long."

        if self.fallproof:
            returndict["terminalvelocity"] = f"'s terminal velocity is {self.terminalvelocity:,.1M} per second ({self.terminalvelocity:,.1U} per second). They can survive a fall from any height!"
        else:
            returndict["terminalvelocity"] = f"'s terminal velocity is {self.terminalvelocity:,.1M} per second ({self.terminalvelocity:,.1U} per second)."

        for k, v in returndict.items():
            returndict[k] = self.tag + v

        return returndict.get(stat)

    def __str__(self):
        return (f"<PersonStats NICKNAME = {self.nickname!r}, TAG = {self.tag!r}, GENDER = {self.gender!r}, "
                f"HEIGHT = {self.height!r}, BASEHEIGHT = {self.baseheight!r}, VIEWSCALE = {self.viewscale!r}, "
                f"WEIGHT = {self.weight!r}, BASEWEIGHT = {self.baseweight!r}, FOOTNAME = {self.footname!r}, "
                f"HAIRNAME = {self.hairname!r}, PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}"
                f"HAIRLENGTH = {self.hairlength!r}, TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r},"
                f"LIFTSTRENGTH = {self.liftstrength!r}, FOOTLENGTH = {self.footlength!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        embed.add_field(name="Current Height", value=f"{self.height:,.3mu}\n*{self.formattedscale} scale*", inline=True)
        embed.add_field(name="Current Weight", value=f"{self.weight:,.3mu}\n*{self.formattedweightscale} scale*", inline=True)
        embed.add_field(name=f"{self.footname} Length", value=f"{self.footlength:.3mu}\n({self.shoesize})", inline=True)
        embed.add_field(name=f"{self.footname} Width", value=format(self.footwidth, ",.3mu"), inline=True)
        embed.add_field(name="Toe Height", value=format(self.toeheight, ",.3mu"), inline=True)
        embed.add_field(name="Shoeprint Depth", value=format(self.shoeprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=format(self.pointerlength, ",.3mu"), inline=True)
        embed.add_field(name="Thumb Width", value=format(self.thumbwidth, ",.3mu"), inline=True)
        embed.add_field(name="Nail Thickness", value=format(self.nailthickness, ",.3mu"), inline=True)
        embed.add_field(name="Fingerprint Depth", value=format(self.fingerprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Clothing Thread Thickness", value=format(self.threadthickness, ",.3mu"), inline=True)
        if self.hairlength:
            embed.add_field(name=f"{self.hairname} Length", value=format(self.hairlength, ",.3mu"), inline=True)
        if self.taillength:
            embed.add_field(name="Tail Length", value=format(self.taillength, ",.3mu"), inline=True)
        if self.earheight:
            embed.add_field(name="Ear Height", value=format(self.earheight, ",.3mu"), inline=True)
        embed.add_field(name=f"{self.hairname} Width", value=format(self.hairwidth, ",.3mu"), inline=True)
        embed.add_field(name="Eye Width", value=format(self.eyewidth, ",.3mu"), inline=True)
        embed.add_field(name="Walk Speed", value=f"{self.walkperhour:,.1M} per hour\n({self.walkperhour:,.1U} per hour)\n[{self.walksteplength:,.1mu} strides]", inline=True)
        embed.add_field(name="Run Speed", value=f"{self.runperhour:,.1M} per hour\n({self.runperhour:,.1U} per hour)\n[{self.runsteplength:,.1mu} strides]", inline=True)
        embed.add_field(name="View Distance to Horizon", value=f"{self.horizondistance:,.3mu}", inline=True)
        if self.fallproof:
            embed.add_field(name="Terminal Velocity", value = f"{self.terminalvelocity:,.1M} per second\n({self.terminalvelocity:,.1U} per second)\n*This user can safely fall from any height.*", inline = True)
        else:
            embed.add_field(name="Terminal Velocity", value = f"{self.terminalvelocity:,.1M} per second\n({self.terminalvelocity:,.1U} per second)", inline = True)
        embed.add_field(name="Lift/Carry Strength", value=f"{self.liftstrength:,.3mu}", inline=True)
        embed.add_field(inline=False)
        embed.add_field(name="Character Bases", value=f"{self.baseheight:,.3mu} | {self.baseweight:,.3mu}", inline=False)
        embed.set_footer(text=f"An average person would look {self.avgheightcomp:,.3mu}, and weigh {self.avgweightcomp:,.3mu} to you. You'd have to look {self.avglookdirection} {self.avglookangle:.0f}° to see them.")
        return embed

class PersonBaseStats:
    def __init__(self, userdata):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.gender = userdata.autogender
        self.baseheight = userdata.baseheight
        self.baseweight = userdata.baseweight
        self.footname = userdata.footname
        self.hairname = userdata.hairname
        self.pawtoggle = userdata.pawtoggle
        self.macrovision_model = userdata.macrovision_model
        self.macrovision_view = userdata.macrovision_view

        self.hairlength = userdata.hairlength
        self.taillength = userdata.taillength
        self.earheight = userdata.earheight
        self.liftstrength = userdata.liftstrength

        self.footlength = userdata.footlength

        if self.footlength:
            self.shoesize = formatShoeSize(self.footlength, self.gender == "f")
        else:
            self.shoesize = None

        self.averageheightmult = self.baseheight / defaultheight
        self.averageweightmult = self.baseweight / defaultweight

        self.walkperhour = userdata.walkperhour
        self.runperhour = userdata.runperhour

        self.currentscalestep = userdata.currentscalestep
        self.unitsystem = userdata.unitsystem


    def __str__(self):
        return (f"<PersonBaseStats NICKNAME = {self.nickname!r}, TAG = {self.tag!r}, GENDER = {self.gender!r}, "
                f"BASEHEIGHT = {self.baseheight!r}, BASEWEIGHT = {self.baseweight!r}, FOOTNAME = {self.footname!r}, "
                f"HAIRNAME = {self.hairname!r}, PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}, "
                f"HAIRLENGTH = {self.hairlength!r}, TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r}, "
                f"LIFTSTRENGTH = {self.liftstrength!r}, FOOTLENGTH = {self.footlength!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Base Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        embed.add_field(name="Base Height", value=f"{self.baseheight:,.3mu}\n*{self.averageheightmult:,.3} average*", inline=True)
        embed.add_field(name="Base Weight", value=f"{self.baseweight:,.3mu}\n*{self.averageweightmult:,.3} average*", inline=True)
        embed.add_field(name="Unit System", value=f"{self.unitsystem.capitalize()}", inline=True)
        if self.footlength:
            embed.add_field(name=f"{self.footname} Length", value=f"{self.footlength:.3mu}\n({self.shoesize})", inline=True)
        if self.hairlength:
            embed.add_field(name=f"{self.hairname} Length", value=format(self.hairlength, ",.3mu"), inline=True)
        if self.taillength:
            embed.add_field(name="Tail Length", value=format(self.taillength, ",.3mu"), inline=True)
        if self.earheight:
            embed.add_field(name="Ear Height", value=format(self.earheight, ",.3mu"), inline=True)
        if self.walkperhour:
            embed.add_field(name="Walk Speed", value=f"{self.walkperhour:,.1M} per hour\n({self.walkperhour:,.1U} per hour)", inline=True)
        if self.runperhour:
            embed.add_field(name="Run Speed", value=f"{self.runperhour:,.1M} per hour\n({self.runperhour:,.1U} per hour)", inline=True)
        if self.liftstrength:
            embed.add_field(name="Lift/Carry Strength", value=f"{self.liftstrength:,.3mu}", inline=True)
        if self.macrovision_model and self.macrovision_model != "Human":
            embed.add_field(name="Macrovision Custom Model", value=f"{self.macrovision_model}, {self.macrovision_view}", inline=True)
        return embed


def formatShoeSize(footlength, women = False):
    # Inch in meters
    inch = Decimal("0.0254")
    footlengthinches = footlength / inch
    shoesizeNum = (3 * (footlengthinches + Decimal("2/3"))) - 24
    prefix = ""
    if shoesizeNum < 1:
        prefix = "Children's "
        shoesizeNum += 12 + Decimal("1/3")
    if shoesizeNum < 0:
        return "No shoes exist this small!"
    if women:
        shoesize = format(Decimal(shoesizeNum + 1), ",.2%2")
    else:
        shoesize = format(Decimal(shoesizeNum), ",.2%2")
    if women:
        return f"Size US Women's {prefix}{shoesize}"
    return f"Size US {prefix}{shoesize}"


def fromShoeSize(shoesize):
    shoesizenum = unmodifiedshoesizenum = Decimal(re.search(r"(\d*,)*\d+(\.\d*)?", shoesize)[0])
    if "w" in shoesize.lower():
        shoesizenum = unmodifiedshoesizenum - 1
    if "c" in shoesize.lower():  # Intentional override, children's sizes have no women/men distinction.
        shoesizenum = unmodifiedshoesizenum - (12 + Decimal("1/3"))
    footlengthinches = ((shoesizenum + 24) / 3) - Decimal("2/3")
    return SV.parse(f"{footlengthinches}in")


def calcViewAngle(viewer, viewee):
    viewer = abs(Decimal(viewer))
    viewee = abs(Decimal(viewee))
    if viewer.is_infinite() and viewee.is_infinite():
        viewer = Decimal(1)
        viewee = Decimal(1)
    elif viewer.is_infinite():
        viewer = Decimal(1)
        viewee = Decimal(0)
    elif viewee.is_infinite():
        viewer = Decimal(0)
        viewee = Decimal(1)
    elif viewee == 0 and viewer == 0:
        viewer = Decimal(1)
        viewee = Decimal(1)
    viewdistance = viewer / 2
    heightdiff = viewee - viewer
    viewangle = Decimal(math.degrees(math.atan(heightdiff / viewdistance)))
    return viewangle
