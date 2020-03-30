from urllib.parse import quote
import math

import discord

from sizebot import __version__
from sizebot.lib import errors, userdb, utils
from sizebot.lib.userdb import defaultheight, defaultweight
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV, WV
from sizebot.lib.constants import emojis

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
    if user.id == user.guild.owner.id:
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

    if userdata.unitsystem in ["m", "u"]:
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
    if user.id == user.guild.owner.id:
        return

    userdata = userdb.load(user.guild.id, user.id)

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

    if changestyle not in ["add", "subtract", "multiply", "divide", "power"]:
        raise errors.ChangeMethodInvalidException(changestyle)

    if changestyle in ["add", "subtract"]:
        amountSV = SV.parse(amount)
    elif changestyle in ["multiply", "divide", "power"]:
        amountVal = Decimal(amount)
        if amountVal == 1:
            raise errors.ValueIsOneException
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

    if changestyle != "power":
        userdata.height = newamount

    userdb.save(userdata)


class PersonComparison:  # TODO: Make a one-sided comparison option.
    def __init__(self, userdata1, userdata2):
        smallUserdata, bigUserdata = utils.minmax(userdata1, userdata2)
        self.big = PersonStats(bigUserdata)
        self.small = PersonStats(smallUserdata)
        self.multiplier = self.big.height / self.small.height

        bigToSmallUserdata = userdb.User()
        bigToSmallUserdata.height = bigUserdata.height * self.small.viewscale
        bigToSmallUserdata.baseweight = bigUserdata.baseweight * self.small.viewscale
        self.bigToSmall = PersonStats(bigToSmallUserdata)

        smallToBigUserdata = userdb.User()
        smallToBigUserdata.height = smallUserdata.height * self.big.viewscale
        smallToBigUserdata.baseweight = smallUserdata.baseweight * self.big.viewscale
        self.smallToBig = PersonStats(smallToBigUserdata)

        viewangle = calcViewAngle(self.small.height, self.big.height)
        self.lookangle = abs(viewangle)
        self.lookdirection = "up" if viewangle >= 0 else "down"

    def __str__(self):
        # Print compare
        returnstr = (
            "**Comparison:**\n"
            f"{self.big.tag} is really:\n"
            f"\tReal Height: {self.big.height:,.3mu} ({self.big.scale:,.3}x scale)\n"
            f"\tReal Weight: {self.big.weight:,.3mu}. ({self.big.scale ** 3:,.3}x scale)\n"
            f"To {self.small.tag}, {self.big.tag} looks:\n"
            f"\tHeight: {self.bigToSmall.height:,.3mu}\n"
            f"\tWeight: {self.bigToSmall.weight:,.3mu}\n"
            f"\tFoot Length: {self.bigToSmall.footlength:,.3mu} ({self.bigToSmall.shoesize})\n"
            f"\tFoot Width: {self.bigToSmall.footwidth:,.3mu}\n"
            f"\tToe Height: {self.bigToSmall.toeheight:,.3mu}\n"
            f"\tShoeprint Depth: {self.bigToSmall.shoeprintdepth:,.3mu}\n"
            f"\tPointer Finger Length: {self.bigToSmall.pointerlength:,.3mu}\n"
            f"\tThumb Width: {self.bigToSmall.thumbwidth:,.3mu}\n"
            f"\tNail Thickness: {self.bigToSmall.nailthickness:,.3mu}\n"
            f"\tFingerprint Depth: {self.bigToSmall.fingerprintdepth:,.3mu}\n"
            f"\tClothing Thread Thickness: {self.bigToSmall.threadthickness:,.3mu}\n")
        if self.bigToSmall.hairlength:
            returnstr += f"\tHair Length: {self.bigToSmall.hairlength:,.3mu}\n"
        returnstr += (
            f"\tHair Width: {self.bigToSmall.hairwidth:,.3mu}\n"
            f"\tEye Width: {self.bigToSmall.eyewidth:,.3mu}\n"
            f"\tWalk Speed: {self.bigToSmall.walkperhour,:.3mu}\n"
            f"\tRun Speed: {self.bigToSmall.runperhour:,.3mu}\n"
            "\n"
            f"{self.big.tag} is {self.multiplier:,.3}x taller than {self.small.tag}.\n"
            "\n"
            f"{self.small.tag} is really:\n"
            f"\tReal Height: {self.small.height:,.3mu} ({self.small.scale:,.3}x scale)\n"
            f"\tReal Weight: {self.small.weight:,.3mu}. ({self.small.scale ** 3:,.3}x scale)\n"
            f"To {self.big.tag}, {self.small.tag} looks:\n"
            f"\tHeight: {self.smallToBig.height:,.3mu}\n"
            f"\tWeight: {self.smallToBig.weight:,.3mu}\n"
            f"\tFoot Length: {self.smallToBig.footlength:,.3mu} ({self.smallToBig.shoesize})\n"
            f"\tFoot Width: {self.smallToBig.footwidth:,.3mu}\n"
            f"\tToe Height: {self.smallToBig.toeheight:,.3mu}\n"
            f"\tShoeprint Depth: {self.smallToBig.shoeprintdepth:,.3mu}\n"
            f"\tPointer Finger Length: {self.smallToBig.pointerlength:,.3mu}\n"
            f"\tThumb Width: {self.smallToBig.thumbwidth:,.3mu}\n"
            f"\tNail Thickness: {self.smallToBig.nailthickness:,.3mu}\n"
            f"\tFingerprint Depth: {self.smallToBig.fingerprintdepth:,.3mu}\n"
            f"\tClothing Thread Thickness: {self.smallToBig.threadthickness:,.3mu}\n")
        if self.smallToBig.hairlength:
            returnstr += f"\tHair Length: {self.smallToBig.hairlength:,.3mu}\n"
        returnstr += (
            f"\tHair Width: {self.smallToBig.hairwidth:,.3mu}\n"
            f"\tEye Width: {self.smallToBig.eyewidth:,.3mu}\n"
            f"\tWalk Speed: {self.smallToBig.walkperhour:,.1M} per hour ({self.smallToBig.walkperhour:,.1U} per hour)\n"
            f"\tRun Speed: {self.smallToBig.runperhour:,.1M} per hour ({self.smallToBig.runperhour:,.1U} per hour)\n"
            "\n"
            f"**Base Sizes:**\n"
            f"\t{self.big.tag}: {self.big.baseheight:,.3mu} | {self.big.baseweight:,.3mu}\n"
            f"\t{self.small.tag}: {self.small.baseheight:,.3mu} | {self.small.baseweight:,.3mu}"
        )
        returnstr = returnstr.replace("\t", "\u2002" * 4)
        return returnstr

    def toEmbed(self):
        embed = discord.Embed(title=f"Comparison of {self.big.nickname} and {self.small.nickname}",
                              description="",
                              color=0x31eff9,
                              url=self.url)
        embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
        embed.add_field(name=f"{emojis.comparebigcenter} **{self.big.nickname}**", value=(
            f"{emojis.blank}{emojis.blank} **Height:** {self.big.height:,.3mu}\n"
            f"{emojis.blank}{emojis.blank} **Weight:** {self.big.weight:,.3mu}\n"), inline=True)
        embed.add_field(name=f"{emojis.comparesmallcenter} **{self.small.nickname}**", value=(
            f"{emojis.blank}{emojis.blank} **Height:** {self.small.height:,.3mu}\n"
            f"{emojis.blank}{emojis.blank} **Weight:** {self.small.weight:,.3mu}\n"), inline=True)
        embed.add_field(name="\u200b", value=(
            f"{emojis.comparebigcenter} looks like {emojis.comparebig} to {emojis.comparesmallcenter}\n"
            f"{emojis.comparesmallcenter} looks like {emojis.comparesmall} to {emojis.comparebigcenter}"), inline=False)
        embed.add_field(name="Height", value=(
            f"{emojis.comparebig}{self.bigToSmall.height:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.height:,.3mu}"), inline=False)
        embed.add_field(name="Weight", value=(
            f"{emojis.comparebig}{self.bigToSmall.weight:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.weight:,.3mu}"), inline=True)
        embed.add_field(name="Foot Length", value=(
            f"{emojis.comparebig}{self.bigToSmall.footlength:,.3mu} ({self.bigToSmall.shoesize})\n"
            f"{emojis.comparesmall}{self.smallToBig.footlength:,.3mu} ({self.smallToBig.shoesize})"), inline=True)
        embed.add_field(name="Foot Width", value=(
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
            embed.add_field(name="Hair Length", value=hairfield, inline=True)
        embed.add_field(name="Hair Width", value=(
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
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}."))
        return embed

    @property
    def url(self):
        gendermap = {
            "m": "male",
            "f": "female",
            None: "male"
        }

        safeSmallNick = quote(self.small.nickname, safe=" ").replace(" ", "-")
        smallGender = gendermap[self.small.gender]
        smallCm = round(self.small.height * 100, 1)
        safeBigNick = quote(self.big.nickname, safe=" ").replace(" ", "-")
        bigGender = gendermap[self.big.gender]
        bigCm = round(self.big.height * 100, 1)

        compUrl = f"http://www.mrinitialman.com/OddsEnds/Sizes/compsizes.xhtml?{safeSmallNick}~{smallGender}~{smallCm}_{safeBigNick}~{bigGender}~{bigCm}"
        return compUrl


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

    def __init__(self, userdata):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.gender = userdata.gender
        self.height = userdata.height
        self.baseheight = userdata.baseheight
        self.viewscale = userdata.viewscale
        self.scale = userdata.scale
        self.baseweight = userdata.baseweight
        self.weight = userdata.weight

        self.averageheightmult = self.height / defaultheight
        self.averageweightmult = self.weight / defaultweight

        if userdata.hairlength is None:
            self.hairlength = None
        else:
            self.hairlength = SV(userdata.hairlength / self.viewscale)

        if userdata.footlength is None:
            self.footlength = SV(self.height * self.footfactor)
        else:
            self.footlength = SV(userdata.footlength / self.viewscale)
        self.shoesize = formatShoeSize(self.footlength)
        self.footwidth = SV(self.height * self.footwidthfactor)
        self.toeheight = SV(self.height * self.toeheightfactor)
        self.shoeprintdepth = SV(self.height * self.toeheightfactor)
        self.pointerlength = SV(self.height * self.pointerfactor)
        self.thumbwidth = SV(self.height * self.thumbfactor)
        self.fingerprintdepth = SV(self.height * self.fingerprintfactor)

        defaultthreadthickness = SV.parse("1.016mm")
        self.threadthickness = SV(defaultthreadthickness * self.averageheightmult)

        self.hairwidth = SV(self.height * self.hairfactor)
        self.nailthickness = SV(self.height * self.nailthickfactor)
        self.eyewidth = SV(self.height * self.eyewidthfactor)

        self.avgheightcomp = SV(defaultheight * self.viewscale)
        self.avgweightcomp = WV(defaultweight * self.viewscale ** 3)

        viewangle = calcViewAngle(self.height, defaultheight)
        self.avglookangle = abs(viewangle)
        self.avglookdirection = "up" if viewangle >= 0 else "down"

        defaultwalkspeed = SV.parse("2.5mi")
        defaultrunspeed = SV.parse("7.5mi")

        self.walkperhour = SV(defaultwalkspeed * self.averageheightmult)
        self.runperhour = SV(defaultrunspeed * self.averageheightmult)

    def __str__(self):
        returnstr = (
            f"**{self.tag} Stats:**\n"
            f"*Current Height:*  {self.height:,.3mu} ({self.averageheightmult:,.3}x average height)\n"
            f"*Current Weight:*  {self.weight:,.3mu} ({self.averageweightmult:,.3}x average weight\n"
            f"\n"
            f"Foot Length: {self.footlength:,.3mu} ({self.shoesize})\n"
            f"Foot Width: {self.footwidth:,.3mu}\n"
            f"Toe Height: {self.toeheight:,.3mu}\n"
            f"Shoeprint Depth: {self.shoeprintdepth:,.3mu}"
            f"Pointer Finger Length: {self.pointerlength:,.3mu}\n"
            f"Thumb Width: {self.thumbwidth:,.3mu}\n"
            f"Nail Thickness: {self.nailthickness:,.3mu}\n"
            f"Fingerprint Depth: {self.fingerprintdepth:,.3mu}\n"
            f"Clothing Thread Thickness: {self.threadthickness:,.3mu}\n")
        if self.hairlength:
            returnstr += f"Hair Length: {self.hairlength:,.3mu}\n"
        returnstr += (
            f"Hair Width: {self.hairwidth:,.3mu}\n"
            f"Eye Width: {self.eyewidth:,.3mu}\n"
            f"Walk Speed: {self.walkperhour:,.1M} per hour ({self.walkperhour:,.1U} per hour)\n"
            f"Run Speed: {self.runperhour:,.1M} per hour ({self.runperhour:,.1U} per hour)\n"
            f"\n"
            f"Size of a Normal Person (Comparative): {self.avgheightcomp:,.3mu}\n"
            f"Weight of a Normal Person (Comparative): {self.avgweightcomp:,.3mu}\n"
            f"To look {self.avglookdirection} at a average human, you'd have to look {self.avglookdirection} {self.avglookangle:.0f}°.\n"
            f"\n"
            f"Character Bases: {self.baseheight:,.3mu} | {self.baseweight:,.3mu}")
        return returnstr

    def toEmbed(self):
        embed = discord.Embed(title=f"Stats for {self.nickname}", color=0x31eff9)
        embed.set_author(name=f"SizeBot {__version__}")
        embed.add_field(name="Current Height", value=f"{self.height:,.3mu}\n({self.averageheightmult:,.3}x average height)", inline=True)
        embed.add_field(name="Current Weight", value=f"{self.weight:,.3mu}\n({self.averageweightmult:,.3}x average weight)", inline=True)
        embed.add_field(name="Foot Length", value=f"{self.footlength:.3mu}\n({self.shoesize})", inline=True)
        embed.add_field(name="Foot Width", value=format(self.footwidth, ",.3mu"), inline=True)
        embed.add_field(name="Toe Height", value=format(self.toeheight, ",.3mu"), inline=True)
        embed.add_field(name="Shoeprint Depth", value=format(self.shoeprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=format(self.pointerlength, ",.3mu"), inline=True)
        embed.add_field(name="Thumb Width", value=format(self.thumbwidth, ",.3mu"), inline=True)
        embed.add_field(name="Nail Thickness", value=format(self.nailthickness, ",.3mu"), inline=True)
        embed.add_field(name="Fingerprint Depth", value=format(self.fingerprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Clothing Thread Thickness", value=format(self.threadthickness, ",.3mu"), inline=True)
        if self.hairlength:
            embed.add_field(name="Hair Length", value=format(self.hairlength, ",.3mu"), inline=True)
        embed.add_field(name="Hair Width", value=format(self.hairwidth, ",.3mu"), inline=True)
        embed.add_field(name="Eye Width", value=format(self.eyewidth, ",.3mu"), inline=True)
        embed.add_field(name="Walk Speed", value=f"{self.walkperhour:,.1M} per hour\n({self.walkperhour:,.1U} per hour)", inline=True)
        embed.add_field(name="Run Speed", value=f"{self.runperhour:,.1M} per hour\n({self.runperhour:,.1U} per hour)", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Character Bases", value=f"{self.baseheight:,.3mu} | {self.baseweight:,.3mu}", inline=False)
        embed.set_footer(text=f"An average person would look {self.avgheightcomp:,.3mu}, and weigh {self.avgweightcomp:,.3mu} to you. You'd have to look {self.avglookdirection} {self.avglookangle:.0f}° to see them.")
        return embed


def formatShoeSize(footlength):
    # Inch in meters
    inch = Decimal("0.0254")
    footlengthinches = footlength / inch
    shoesizeNum = (3 * (footlengthinches + Decimal("2/3"))) - 24
    prefix = ""
    if shoesizeNum < 1:
        prefix = "Children's "
        shoesizeNum += 12 + Decimal("1/3")
    if shoesizeNum < 1:
        return "No shoes exist this small!"
    shoesize = format(Decimal(shoesizeNum), ",.2%2")
    return f"Size US {prefix}{shoesize}"


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
