import math

import discord

from sizebot.digidecimal import Decimal, roundDecimalHalf
from sizebot import digierror as errors
from sizebot.digiSV import SV, WV
from sizebot import userdb
from sizebot.userdb import defaultheight, defaultweight
from sizebot import utils


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


# Remove sizetag from user's nickname
async def nickReset(user):
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
        bigUserdata = userdata1 if userdata1.height > userdata2.height else userdata2
        smallUserdata = userdata2 if userdata2.height > userdata1.height else userdata1
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

    def __str__(self):
        # Print compare
        enspace = "\u2002"
        printtab = enspace * 4
        return (
            "**Comparison:**\n"
            f"{self.big.tag} is really:\n"
            f"{printtab}Real Height: {self.big.height:.3m} / {self.big.height:.3u} ({self.big.basemultiplier:,}x basesize)\n"
            f"{printtab}Real Weight: {self.big.weight:.3m} / {self.big.weight:.3u}. ({self.big.basemultiplier ** 3:,}x basesize)\n"
            f"To {self.small.tag}, {self.big.tag} looks:\n"
            f"{printtab}Height: {self.bigToSmall.height:.3m} / {self.bigToSmall.height:.3u}\n"
            f"{printtab}Weight: {self.bigToSmall.weight:.3m} / {self.bigToSmall.weight:.3u}\n"
            f"{printtab}Foot Length: {self.bigToSmall.footlength:.3m} / {self.bigToSmall.footlength:.3u} ({self.bigToSmall.shoesize})\n"
            f"{printtab}Foot Width: {self.bigToSmall.footwidth:.3m} / {self.bigToSmall.footwidth:.3u}\n"
            f"{printtab}Toe Height: {self.bigToSmall.toeheight:.3m} / {self.bigToSmall.toeheight:.3u}\n"
            f"{printtab}Pointer Finger Length: {self.bigToSmall.pointerlength:.3m} / {self.bigToSmall.pointerlength:.3u}\n"
            f"{printtab}Thumb Width: {self.bigToSmall.thumbwidth:.3m} / {self.bigToSmall.thumbwidth:.3u}\n"
            f"{printtab}Fingerprint Depth: {self.bigToSmall.fingerprintdepth:.3m} / {self.bigToSmall.fingerprintdepth:.3u}\n"
            f"{printtab}Hair Width: {self.bigToSmall.hairwidth:.3m} / {self.bigToSmall.hairwidth:.3u}\n"
            "\n"
            f"{self.big.tag} is {self.multiplier:,.3}x taller than {self.small.tag}.\n"
            "\n"
            f"{self.small.tag} is really:\n"
            f"{printtab}Real Height: {self.small.height:.3m} / {self.small.height:u} ({self.small.basemultiplier:,}x basesize)\n"
            f"{printtab}Real Weight: {self.small.weight:.3m} / {self.small.weight:.3u}. ({self.small.basemultiplier ** 3:,}x basesize)\n"
            f"To {self.big.tag}, {self.small.tag} looks:\n"
            f"{printtab}Height: {self.smallToBig.height:.3m} / {self.smallToBig.height:.3u}\n"
            f"{printtab}Weight: {self.smallToBig.weight:.3m} / {self.smallToBig.weight:.3u}\n"
            f"{printtab}Foot Length: {self.smallToBig.footlength:.3m} / {self.smallToBig.footlength:.3u} ({self.smallToBig.shoesize})\n"
            f"{printtab}Foot Width: {self.smallToBig.footwidth:.3m} / {self.smallToBig.footwidth:.3u}\n"
            f"{printtab}Toe Height: {self.smallToBig.toeheight:.3m} / {self.smallToBig.toeheight:.3u}\n"
            f"{printtab}Pointer Finger Length: {self.smallToBig.pointerlength:.3m} / {self.smallToBig.pointerlength:.3u}\n"
            f"{printtab}Thumb Width: {self.smallToBig.thumbwidth:.3m} / {self.smallToBig.thumbwidth:.3u}\n"
            f"{printtab}Fingerprint Depth: {self.smallToBig.fingerprintdepth:.3m} / {self.smallToBig.fingerprintdepth:.3u}\n"
            f"{printtab}Hair Width: {self.smallToBig.hairwidth:.3m} / {self.smallToBig.hairwidth:.3u}\n"
            "\n"
            f"**Base Sizes:**\n"
            f"{printtab}{self.big.tag}: {self.big.baseheight:.3m} / {self.big.baseheight:.3u} | {self.big.baseweight:.3m} / {self.big.baseweight:.3u}\n"
            f"{printtab}{self.small.tag}: {self.small.baseheight:.3m} / {self.small.baseheight:.3u} | {self.small.baseweight:.3m} / {self.small.baseweight:.3u}"
        )


class PersonStats():
    # Conversion constants
    footfactor = Decimal("1") / Decimal("7")
    footwidthfactor = footfactor / Decimal("2.5")
    toeheightfactor = Decimal("1") / Decimal("65")
    thumbfactor = Decimal("1") / Decimal("69.06")
    fingerprintfactor = Decimal("1") / Decimal("35080")
    hairfactor = Decimal("1") / Decimal("23387")
    pointerfactor = Decimal("1") / Decimal("17.26")
    footthickfactor = Decimal("1")  # TODO: Provide a real value
    hairwidthfactor = Decimal("1")  # TODO: Provide a real value

    def __init__(self, userdata):
        self.tag = userdata.tag
        self.height = userdata.height
        self.baseheight = userdata.baseheight
        self.basemultiplier = self.height / self.baseheight
        self.baseweight = userdata.baseweight
        self.weight = WV(self.baseweight * self.basemultiplier ** 3)
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
            f"*Current Height:*  {self.height:.3m} / {self.height:.3u}\n"
            f"*Current Weight:*  {self.weight:.3m} / {self.weight:.3u}\n"
            f"\n"
            f"Foot Length: {self.footlength:.3m} / {self.footlength:.3u}\n"
            f"Foot Width: {self.footwidth:.3m} / {self.footwidth:.3u}\n"
            f"Toe Height: {self.toeheight:.3m} / {self.toeheight:.3u}\n"
            f"Pointer Finger Length: {self.pointerlength:.3m} / {self.pointerlength:.3u}\n"
            f"Thumb Width: {self.thumbwidth:.3m} / {self.thumbwidth:.3u}\n"
            f"Fingerprint Depth: {self.fingerprintdepth:.3m} / {self.fingerprintdepth:.3u}\n"
            f"Hair Width: {self.hairwidth:.3m} / {self.hairwidth:.3u}\n"
            f"\n"
            f"Size of a Normal Man (Comparative): {self.avgheightcomp:.3m} / {self.avgheightcomp:.3u}\n"
            f"Weight of a Normal Man (Comparative): {self.avgweightcomp:.3u} / {self.avgweightcomp:.3u}\n"
            f"To look {self.avglookdirection} at a average human, you'd have to look {self.avglookdirection} {self.avglookangle:.0f}°.\n"
            f"\n"
            f"Character Bases: {self.baseheight:.3m} / {self.baseheight:.3u} | {self.baseweight:.3m} / {self.baseweight:.3u}"
        )


def getStats(userdata):
    return PersonStats(userdata)


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
        formatSpec = ",.1"
    shoesize = format(roundDecimalHalf(shoesizeNum), formatSpec)
    return f"Size US {prefix}{shoesize}"
