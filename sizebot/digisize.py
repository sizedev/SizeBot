from urllib.parse import quote
import math

import discord

from sizebot.conf import conf
from sizebot.digidecimal import Decimal, roundDecimalHalf, roundDecimal
from sizebot import digierror as errors
from sizebot.digiSV import SV, WV
from sizebot import userdb
from sizebot.userdb import defaultheight, defaultweight
from sizebot import utils

emojis = {"compare" : "<:Compare:665019546289176597>",
          "comparebig" : "<:CompareBig:665019546847019031>",
          "comparesmall" : "<:CompareSmall:665019546780041286>",
          "comparesmallbig" : "<:CompareSmallBig:665019546490503180>",
          "comparebigcenter" : "<:CompareBigCenter:665021475475947520>",
          "comparesmallcenter" : "<:CompareSmallCenter:665021475375415306>"}
compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"


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
        userdata = userdb.load(user.id)
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
        sizetag = format(height, userdata.unitsystem)
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

    userdata = userdb.load(user.id)

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    try:
        await user.edit(nick = userdata.nickname)
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
        raise errors.ChangeMethodInvalidException(changestyle)
        # TODO: raise an error

    if changestyle in ["add", "subtract"]:
        amountSV = SV.parse(amount)
    elif changestyle in ["multiply", "divide"]:
        amountVal = Decimal(amount)
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

    userdata.height = utils.clamp(0, newamount, SV.infinity)

    userdb.save(userdata)


class PersonComparison:
    def __init__(self, userdata1, userdata2):
        smallUserdata, bigUserdata = utils.minmax(userdata1, userdata2)
        self.big = PersonStats(bigUserdata)
        self.small = PersonStats(smallUserdata)
        self.multiplier = self.big.height / self.small.height

        bigToSmallUserdata = userdb.User()
        bigToSmallUserdata.height = bigUserdata.height * self.multiplier
        bigToSmallUserdata.baseweight = bigUserdata.baseweight * self.multiplier
        self.bigToSmall = PersonStats(bigToSmallUserdata)

        smallToBigUserdata = userdb.User()
        smallToBigUserdata.height = smallUserdata.height / self.multiplier
        smallToBigUserdata.baseweight = smallUserdata.baseweight / self.multiplier
        self.smallToBig = PersonStats(smallToBigUserdata)

        self.lookangle, self.lookdirection = look(self.small.height, self.big.height)

    def __str__(self):
        # Print compare
        enspace = "\u2002"
        printtab = enspace * 4
        return (
            "**Comparison:**\n"
            f"{self.big.tag} is really:\n"
            f"{printtab}Real Height: {self.big.height:.3mu} ({self.big.basemultiplier:,}x basesize)\n"
            f"{printtab}Real Weight: {self.big.weight:.3mu}. ({self.big.basemultiplier ** 3:,}x basesize)\n"
            f"To {self.small.tag}, {self.big.tag} looks:\n"
            f"{printtab}Height: {self.bigToSmall.height:.3mu}\n"
            f"{printtab}Weight: {self.bigToSmall.weight:.3mu}\n"
            f"{printtab}Foot Length: {self.bigToSmall.footlength:.3mu} ({self.bigToSmall.shoesize})\n"
            f"{printtab}Foot Width: {self.bigToSmall.footwidth:.3mu}\n"
            f"{printtab}Toe Height: {self.bigToSmall.toeheight:.3mu}\n"
            f"{printtab}Pointer Finger Length: {self.bigToSmall.pointerlength:.3mu}\n"
            f"{printtab}Thumb Width: {self.bigToSmall.thumbwidth:.3mu}\n"
            f"{printtab}Fingerprint Depth: {self.bigToSmall.fingerprintdepth:.3mu}\n"
            f"{printtab}Hair Width: {self.bigToSmall.hairwidth:.3mu}\n"
            "\n"
            f"{self.big.tag} is {self.multiplier:,.3}x taller than {self.small.tag}.\n"
            "\n"
            f"{self.small.tag} is really:\n"
            f"{printtab}Real Height: {self.small.height:.3mu} ({self.small.basemultiplier:,}x basesize)\n"
            f"{printtab}Real Weight: {self.small.weight:.3mu}. ({self.small.basemultiplier ** 3:,}x basesize)\n"
            f"To {self.big.tag}, {self.small.tag} looks:\n"
            f"{printtab}Height: {self.smallToBig.height:.3mu}\n"
            f"{printtab}Weight: {self.smallToBig.weight:.3mu}\n"
            f"{printtab}Foot Length: {self.smallToBig.footlength:.3mu} ({self.smallToBig.shoesize})\n"
            f"{printtab}Foot Width: {self.smallToBig.footwidth:.3mu}\n"
            f"{printtab}Toe Height: {self.smallToBig.toeheight:.3mu}\n"
            f"{printtab}Pointer Finger Length: {self.smallToBig.pointerlength:.3mu}\n"
            f"{printtab}Thumb Width: {self.smallToBig.thumbwidth:.3mu}\n"
            f"{printtab}Fingerprint Depth: {self.smallToBig.fingerprintdepth:.3mu}\n"
            f"{printtab}Hair Width: {self.smallToBig.hairwidth:.3mu}\n"
            "\n"
            f"**Base Sizes:**\n"
            f"{printtab}{self.big.tag}: {self.big.baseheight:.3m3u} | {self.big.baseweight:.3mu}\n"
            f"{printtab}{self.small.tag}: {self.small.baseheight:.3mu} | {self.small.baseweight:.3mu}"
        )

    def toEmbed(self):
        embed = discord.Embed(title=f"Comparison of {self.big.nickname} and {self.small.nickname}",
                              description=(f"{emojis['compareBigCenter']} {self.big.nickname}: {self.big.height:.3mu} | {self.big.weight:.3mu}\n"
                                           f"{emojis['compareSmallCenter']} {self.small.nickname}: {self.small.height:.3mu} | {self.small.weight:.3mu}\n"
                                           f"{emojis['compareBigCenter']} is {self.multiplier:,.3}x taller than {emojis['compareSmallCenter']}."),
                              color=0x31eff9)
        embed.set_author(name=f"SizeBot {conf.version}")
        embed.set_thumbnail(url = compareicon)
        embed.add_field(name="Height", value=(f"{emojis['comparebig']}{self.bigToSmall.height:.3mu}\n"
                                              f"{emojis['comparesmall']}{self.smallToBig.height:.3mu}"), inline=True)
        embed.add_field(name="Weight", value=(f"{emojis['comparebig']}{self.bigToSmall.weight:.3mu}\n"
                                              f"{emojis['comparesmall']}{self.smallToBig.weight:.3mu}"), inline=True)
        embed.add_field(name="Foot Length", value=(f"{emojis['comparebig']}{self.bigToSmall.footlength:.3mu}\n"
                                                   f"{emojis['comparesmall']}{self.smallToBig.footlength:.3mu}"), inline=True)
        embed.add_field(name="Foot Width", value=(f"{emojis['comparebig']}{self.bigToSmall.footwidth:.3mu}\n"
                                                  f"{emojis['comparesmall']}{self.smallToBig.footwidth:.3mu}"), inline=True)
        embed.add_field(name="Toe Height", value=(f"{emojis['comparebig']}{self.bigToSmall.toeheigh:.3mut}\n"
                                                  f"{emojis['comparesmall']}{self.smallToBig.toeheight:.3mu}"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=(f"{emojis['comparebig']}{self.bigToSmall.pointerlength:.3mu}\n"
                                                             f"{emojis['comparesmall']}{self.smallToBig.pointerlength:.3mu}"), inline=True)
        embed.add_field(name="Thumb Width", value=(f"{emojis['comparebig']}{self.bigToSmall.thumbwidth:.3mu}\n"
                                                   f"{emojis['comparesmall']}{self.smallToBig.thumbwidth:.3mu}"), inline=True)
        embed.add_field(name="Fingerprint Depth", value=(f"{emojis['comparebig']}{self.bigToSmall.fingerprintdepth:.3mu}\n"
                                                         f"{emojis['comparesmall']}{self.smallToBig.fingerprintdepth:.3mu}"), inline=True)
        embed.add_field(name="Hair Width", value=(f"{emojis['comparebig']}{self.bigToSmall.hairwidth:.3mu}\n"
                                                  f"{emojis['comparesmall']}{self.smallToBig.hairwidth:.3mu}"), inline=True)
        embed.set_footer(text=f"{emojis['comparesmall']} would have to look {self.lookdirection} {self.lookangle:.0f}° at {emojis['comparebig']}")
        return embed

    @property
    def url(self):
        safeSmallNick = quote(self.small.nickname, safe=" ").replace(" ", "-")
        smallCm = roundDecimal(self.small.height * 100, 1)
        safeBigNick = quote(self.big.nickname, safe=" ").replace(" ", "-")
        bigCm = roundDecimal(self.big.height * 100, 1)
        compUrl = f"http://www.mrinitialman.com/OddsEnds/Sizes/compsizes.xhtml?{safeSmallNick}~male~{smallCm}_{safeBigNick}~male~{bigCm}"
        return compUrl


class PersonStats:
    # Conversion constants
    footfactor = Decimal("1") / Decimal("7")
    footwidthfactor = footfactor / Decimal("2.5")
    toeheightfactor = Decimal("1") / Decimal("65")
    thumbfactor = Decimal("1") / Decimal("69.06")
    fingerprintfactor = Decimal("1") / Decimal("35080")
    hairfactor = Decimal("1") / Decimal("23387")
    pointerfactor = Decimal("1") / Decimal("17.26")

    def __init__(self, userdata):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.height = userdata.height
        self.baseheight = userdata.baseheight
        self.basemultiplier = self.height / self.baseheight
        self.baseweight = userdata.baseweight
        self.weight = WV(self.baseweight * self.basemultiplier ** 3)
        self.footlength = userdata.footlength
        if self.footlength is None:
            self.footlength = SV(self.height * self.footfactor)
        self.shoesize = formatShoeSize(self.footlength)
        self.footwidth = SV(self.height * self.footwidthfactor)
        self.toeheight = SV(self.height * self.toeheightfactor)
        self.pointerlength = SV(self.height * self.pointerfactor)
        self.thumbwidth = SV(self.height * self.thumbfactor)
        self.fingerprintdepth = SV(self.height * self.fingerprintfactor)
        self.hairwidth = SV(self.height * self.hairfactor)

        self.avgheightcomp = SV(defaultheight / self.basemultiplier)
        self.avgweightcomp = WV(defaultweight / self.basemultiplier ** 3)
        self.avglookdirection = "down" if self.height >= defaultheight else "up"
        # angle the smaller person must look up if they are standing half of the taller person's height away
        heightdiff = abs(userdata.height - defaultheight)
        viewdistance = max(userdata.height, defaultheight) / 2
        self.avglookangle = math.degrees(math.atan(heightdiff / viewdistance))

    def __str__(self):
        return (
            f"**{self.tag} Stats:**\n"
            f"*Current Height:*  {self.height:,.3mu}\n"
            f"*Current Weight:*  {self.weight:,.3mu}\n"
            f"\n"
            f"Foot Length: {self.footlength:,.3mu}\n"
            f"Foot Width: {self.footwidth:,.3mu}\n"
            f"Toe Height: {self.toeheight:,.3mu}\n"
            f"Pointer Finger Length: {self.pointerlength:,.3mu}\n"
            f"Thumb Width: {self.thumbwidth:,.3mu}\n"
            f"Fingerprint Depth: {self.fingerprintdepth:,.3mu}\n"
            f"Hair Width: {self.hairwidth:,.3mu}\n"
            f"\n"
            f"Size of a Normal Man (Comparative): {self.avgheightcomp:,.3mu}\n"
            f"Weight of a Normal Man (Comparative): {self.avgweightcomp:,.3mu}\n"
            f"To look {self.avglookdirection} at a average human, you'd have to look {self.avglookdirection} {self.avglookangle:.0f}°.\n"
            f"\n"
            f"Character Bases: {self.baseheight:,.3mu} | {self.baseweight:,.3mu}"
        )

    def toEmbed(self):
        embed = discord.Embed(title=f"Stats for {self.nickname}", color=0x31eff9)
        embed.set_author(name=f"SizeBot {conf.version}")
        embed.add_field(name="Current Height", value=format(self.height, ",.3mu"), inline=True)
        embed.add_field(name="Current Weight", value=format(self.weight, ",.3mu"), inline=True)
        embed.add_field(name="Foot Length", value=format(self.footlength, ",.3mu"), inline=True)
        embed.add_field(name="Foot Width", value=format(self.footwidth, ",.3mu"), inline=True)
        embed.add_field(name="Toe Height", value=format(self.toeheight, ",.3mu"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=format(self.pointerlength, ",.3mu"), inline=True)
        embed.add_field(name="Thumb Width", value=format(self.thumbwidth, ",.3mu"), inline=True)
        embed.add_field(name="Fingerprint Depth", value=format(self.fingerprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Hair Width", value=format(self.hairwidth, ",.3mu"), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Character Bases", value=f"{self.baseheight:,.3mu} | {self.baseweight:,.3mu}", inline=False)
        embed.set_footer(text=f"An average human would look {self.avgheightcomp:,.3mu}, and weigh {self.avgweightcomp:,.3mu} to you. You'd have to look {self.avglookdirection} {self.avglookangle:.0f}° to see them.")
        return embed


def formatShoeSize(footlength):
    footlengthinches = Decimal(footlength / SV.inch)
    shoesizeNum = (3 * footlengthinches) - 22
    prefix = ""
    if shoesizeNum < 1:
        prefix = "Children's "
        shoesizeNum += 12 + Decimal(1) / Decimal(3)
    if shoesizeNum < 1:
        return "No shoes exist this small!"
    if shoesizeNum > Decimal("1E15"):
        formatSpec = ".2e"
    else:
        formatSpec = ",.1f"
    rounded = roundDecimalHalf(shoesizeNum)
    shoesize = format(rounded, formatSpec)
    return f"Size US {prefix}{shoesize}"


def look(height1, height2):
    lookdirection = "down" if height1 >= height2 else "up"
    # angle the smaller person must look up if they are standing half of the taller person's height away
    heightdiff = abs(height1 - height2)
    viewdistance = max(height1, height2) / 2
    lookangle = math.degrees(math.atan(heightdiff / viewdistance))
    return lookdirection, lookangle
