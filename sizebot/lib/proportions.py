from __future__ import annotations

from copy import copy
from typing import Literal
import math
import re

from discord import Embed

from sizebot import __version__
from sizebot.lib import errors, macrovision, userdb, utils
from sizebot.lib.constants import colors, emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import User, DEFAULT_HEIGHT as average_height, DEFAULT_WEIGHT
from sizebot.lib.utils import minmax, pretty_time_delta, url_safe
from sizebot.lib.stats import statmap, StatBox

AVERAGE_HEIGHT = average_height
AVERAGE_WALKPERHOUR = SV(5630)


compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"


def change_user(guildid: int, userid: int, changestyle: str, amount: SV):
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
    def __init__(self, userdata1: User, userdata2: User):
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
            title=f"Comparison of {self.big.nickname} and {self.small.nickname} {emojis.link}",
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
            f"{emojis.comparebig}{self.bigToSmall.footlength:,.3mu}\n({self.bigToSmall.shoesize})\n"
            f"{emojis.comparesmall}{self.smallToBig.footlength:,.3mu}\n({self.smallToBig.shoesize})"), inline=True)
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
                hairfield += f"{emojis.comparesmall}{self.smallToBig.hairlength:,.3mu}\n"
            hairfield = hairfield.strip()
            embed.add_field(name=f"{self.hairlabel} Length", value=hairfield, inline=True)
        if self.bigToSmall.taillength or self.smallToBig.taillength:
            tailfield = ""
            if self.bigToSmall.taillength:
                tailfield += f"{emojis.comparebig}{self.bigToSmall.taillength:,.3mu}\n"
            if self.smallToBig.taillength:
                tailfield += f"{emojis.comparesmall}{self.smallToBig.taillength:,.3mu}\n"
            tailfield = tailfield.strip()
            embed.add_field(name="Tail Length", value=tailfield, inline=True)
        if self.bigToSmall.earheight or self.smallToBig.earheight:
            earfield = ""
            if self.bigToSmall.earheight:
                earfield += f"{emojis.comparebig}{self.bigToSmall.earheight:,.3mu}\n"
            if self.smallToBig.earheight:
                earfield += f"{emojis.comparesmall}{self.smallToBig.earheight:,.3mu}\n"
            earfield = earfield.strip()
            embed.add_field(name="Ear Height", value=earfield, inline=True)
        embed.add_field(name=f"{self.hairlabel} Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.hairwidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.hairwidth:,.3mu}"), inline=True)
        embed.add_field(name="Eye Width", value=(
            f"{emojis.comparebig}{self.bigToSmall.eyewidth:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.eyewidth:,.3mu}"), inline=True)
        embed.add_field(name="Jump Height", value=(
            f"{emojis.comparebig}{self.bigToSmall.jumpheight:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.jumpheight:,.3mu}"), inline=True)
        embed.add_field(name="Lift/Carry Strength", value=(
            f"{emojis.comparebig}{self.bigToSmall.liftstrength:,.3mu}\n"
            f"{emojis.comparesmall}{self.smallToBig.liftstrength:,.3mu}"), inline=True)
        embed.add_field(name=f"{emojis.comparebig} Speeds", value=self.bigToSmall.simplespeeds, inline=False)
        embed.add_field(name=f"{emojis.comparesmall} Speeds", value=self.smallToBig.simplespeeds, inline=False)
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}.\n"
            f"{self.big.nickname} would need {self.smallToBig.visibility} to see {self.small.nickname}."))

        return embed

    async def toSimpleEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(
            title=f"Comparison of {self.big.nickname} and {self.small.nickname} {emojis.link}",
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
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}.\n"
            f"{self.big.nickname} would need {self.smallToBig.visibility} to see {self.small.nickname}."))

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
    def __init__(self, userdata1: User, userdata2: User):
        self._viewer, self._viewed = minmax(userdata1, userdata2)

        self.viewer = PersonStats(self._viewer)
        self.viewed = PersonStats(self._viewed)

        self.viewertovieweddata = copy(self._viewer)
        self.viewedtoviewerdata = copy(self._viewed)

        if self.viewer.height == 0 and self.viewed.height == 0:
            self.multiplier = Decimal(1)
        else:
            self.multiplier = self.viewed.height / self.viewer.height

        self.viewedtoviewer = PersonStats(self.viewedtoviewerdata)
        self.viewertoviewed = PersonStats(self.viewertovieweddata)

        self.footlabel = "Paw" if self.viewed.pawtoggle else "Foot"
        self.hairlabel = "Fur" if self.viewed.furtoggle else "Hair"

        viewangle = calcViewAngle(self.viewer.height, self.viewed.height)
        self.lookangle = abs(viewangle)
        self.lookdirection = "up" if viewangle >= 0 else "down"

    def __str__(self):
        return f"<PersonSpeedComparison VIEWER = {self.viewer!r}, VIEWED = {self.viewed!r}, \
            VIEWERTOVIEWED = {self.viewertoviewed!r}, VIEWEDTOVIEWER = {self.viewedtoviewer!r}>"

    def __repr__(self):
        return str(self)

    def speedcalc(self, dist: SV, *, speed = False, foot = False, include_relative = False):
        reldist = SV(dist * self.viewer.viewscale)
        reldist_print = f"{reldist:,.3mu}"
        shoesize = " (" + format_shoe_size(dist, "m") + ")"
        rel_shoesize = " (" + format_shoe_size(reldist, "m") + ")"

        _walktime = (dist / self.viewer.walkperhour) * 60 * 60
        walksteps = math.ceil(dist / self.viewer.walksteplength)
        _runtime = (dist / self.viewer.runperhour) * 60 * 60
        runsteps = math.ceil(dist / self.viewer.runsteplength)
        _climbtime = (dist / self.viewer.climbperhour) * 60 * 60
        climbsteps = math.ceil(dist / self.viewer.climbsteplength)
        _crawltime = (dist / self.viewer.crawlperhour) * 60 * 60
        crawlsteps = math.ceil(dist / self.viewer.crawlsteplength)
        _swimtime = (dist / self.viewer.swimperhour) * 60 * 60
        swimsteps = math.ceil(dist / self.viewer.swimsteplength)
        _drivetime = (dist / self.viewer.driveperhour) * 60 * 60
        _spaceshiptime = (dist / self.viewer.spaceshipperhour) * 60 * 60
        walktime = pretty_time_delta(_walktime, roundeventually = True)
        runtime = pretty_time_delta(_runtime, roundeventually = True)
        climbtime = pretty_time_delta(_climbtime, roundeventually = True)
        crawltime = pretty_time_delta(_crawltime, roundeventually = True)
        swimtime = pretty_time_delta(_swimtime, roundeventually = True)
        drivetime = pretty_time_delta(_drivetime, roundeventually = True)
        spaceshiptime = pretty_time_delta(_spaceshiptime, roundeventually = True)

        walkspeedstr = f"\n*{emojis.blank}{self.viewer.walkperhour:,.3mu} per hour*"
        runspeedstr = f"\n*{emojis.blank}{self.viewer.runperhour:,.3mu} per hour*"
        climbspeedstr = f"\n*{emojis.blank}{self.viewer.climbperhour:,.3mu} per hour*"
        crawlspeedstr = f"\n*{emojis.blank}{self.viewer.crawlperhour:,.3mu} per hour*"
        swimspeedstr = f"\n*{emojis.blank}{self.viewer.swimperhour:,.3mu} per hour*"
        drivespeedstr = f"\n*{emojis.blank}{self.viewer.driveperhour:,.3mu} per hour*"
        spacespeedstr = f"\n*{emojis.blank}{self.viewer.spaceshipperhour:,.3mu} per hour*"

        nl = "\n"

        out_str = (
            f"{emojis.ruler} {dist:,.3mu}{shoesize if foot else ''}\n"
            f"{emojis.eyes + ' ' + reldist_print + nl if include_relative else ''}{emojis.blank + rel_shoesize + nl if foot and include_relative else ''}"
            f"{emojis.walk} {walktime} ({walksteps:,.3} steps){walkspeedstr if speed else ''}\n"
        )
        if _runtime >= 1:
            out_str += f"{emojis.run} {runtime} ({runsteps:,.3} strides){runspeedstr if speed else ''}\n"

        out_str += f"{emojis.climb} {climbtime} ({climbsteps:,.3} pulls){climbspeedstr if speed else ''}\n"
        if _crawltime >= 1:
            out_str += f"{emojis.crawl} {crawltime} ({crawlsteps:,.3} steps){crawlspeedstr if speed else ''}\n"
        if _swimtime >= 1:
            out_str += f"{emojis.swim} {swimtime} ({swimsteps:,.3} strokes){swimspeedstr if speed else ''}\n"
        if _drivetime >= 1:
            out_str += f"{emojis.drive} {drivetime} {drivespeedstr if speed else ''}\n"
        if _spaceshiptime >= 1:
            out_str += f"{emojis.spaceship} {spaceshiptime} {spacespeedstr if speed else ''}\n"

        return out_str.strip()

    def getStatEmbed(self, key: str):
        try:
            mapped_key = statmap[key]
        except KeyError:
            return None

        # TODO: Make this dynamically?
        descmap = {
            "height":           self.speedcalc(self.viewedtoviewer.height, speed = True, include_relative = True),
            "footlength":       self.speedcalc(self.viewedtoviewer.footlength, speed = True, foot = True, include_relative = True),
            "toeheight":        self.speedcalc(self.viewedtoviewer.toeheight, speed = True, include_relative = True),
            "shoeprintdepth":   self.speedcalc(self.viewedtoviewer.shoeprintdepth, speed = True, include_relative = True),
            "fingerlength":     self.speedcalc(self.viewedtoviewer.pointerlength, speed = True, include_relative = True),
            "fingerprintdepth": self.speedcalc(self.viewedtoviewer.fingerprintdepth, speed = True, include_relative = True),
            "thumbwidth":       self.speedcalc(self.viewedtoviewer.thumbwidth, speed = True, include_relative = True),
            "eyewidth":         self.speedcalc(self.viewedtoviewer.eyewidth, speed = True, include_relative = True),
            "hairwidth":        self.speedcalc(self.viewedtoviewer.hairwidth, speed = True, include_relative = True),
            "hairlength":       self.speedcalc(self.viewedtoviewer.hairlength, speed = True, include_relative = True) if self.viewedtoviewer.hairlength is not None else None,
            "taillength":       self.speedcalc(self.viewedtoviewer.taillength, speed = True, include_relative = True) if self.viewedtoviewer.taillength is not None else None,
            "earheight":        self.speedcalc(self.viewedtoviewer.earheight, speed = True, include_relative = True) if self.viewedtoviewer.earheight is not None else None
        }

        if descmap[mapped_key] is None:
            return None

        statnamemap = {
            "height":           "Height",
            "footlength":       f"{self.viewed.footname} Length",
            "toeheight":        "Toe Height",
            "shoeprintdepth":   "Shoeprint Depth",
            "fingerlength":     "Finger Length",
            "thumbwidth":       "Thumb Width",
            "fingerprintdepth": "Fingerprint Depth",
            "eyewidth":         "Eye Width",
            "hairwidth":        f"{self.viewed.hairname} Width",
            "hairlength":       f"{self.viewed.hairname} Length",
            "taillength":       "Tail Length",
            "earheight":        "Ear Height",
        }

        statname = statnamemap[mapped_key].replace("Foot", self.viewertovieweddata.footname) \
                                          .replace("Hair", self.viewertovieweddata.hairname) \
                                          .lower()

        desc = descmap[mapped_key]

        return Embed(
            title = f"To move the distance of {self.viewedtoviewerdata.nickname}'s {statname}, it would take {self.viewertovieweddata.nickname}...",
            description = desc)

    async def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(
            title=f"Speed/Distance Comparison of {self.viewed.nickname} and {self.viewer.nickname}",
            description=f"*Requested by {requestertag}*",
            color=colors.purple
        )
        embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
        embed.add_field(name=f"**{self.viewer.nickname}** Speeds", value=(
            f"{emojis.walk} **Walk Speed:** {self.viewer.walkperhour:,.3mu} per hour\n"
            f"{emojis.run} **Run Speed:** {self.viewer.runperhour:,.3mu} per hour\n"
            f"{emojis.climb} **Climb Speed:** {self.viewer.climbperhour:,.3mu} per hour\n"
            f"{emojis.crawl} **Crawl Speed:** {self.viewer.crawlperhour:,.3mu} per hour\n"
            f"{emojis.swim} **Swim Speed:** {self.viewer.swimperhour:,.3mu} per hour"), inline=False)
        embed.add_field(name="Height", value=(self.speedcalc(self.viewedtoviewer.height)), inline=True)
        embed.add_field(name=f"{self.footlabel} Length", value=(self.speedcalc(self.viewedtoviewer.footlength, foot = True)), inline=True)
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
            embed.add_field(name="Tail Length", value=(self.speedcalc(self.viewedtoviewer.taillength)), inline=True)
        if self.viewedtoviewer.earheight:
            embed.add_field(name="Ear Height", value=(self.speedcalc(self.viewedtoviewer.earheight)), inline=True)
        embed.add_field(name=f"{self.hairlabel} Width", value=(self.speedcalc(self.viewedtoviewer.hairwidth)), inline=True)
        embed.add_field(name="Eye Width", value=(self.speedcalc(self.viewedtoviewer.eyewidth)), inline=True)
        embed.set_footer(text=(f"{self.viewed.nickname} is {self.multiplier:,.3}x taller than {self.viewer.nickname}."))

        return embed


class PersonStats:
    def __init__(self, userdata: User):
        self.nickname = userdata.nickname                               # USED
        self.tag = userdata.tag                                         # UNUSED

        # Use the new statbox
        self.basestats = StatBox.load(userdata.stats)                   # UNUSED
        self.stats = self.basestats.scale(userdata.scale)               # UNUSED

        # TODO: There's not a good way of getting these yet:

        self.viewscale = userdata.viewscale                             # USED
        self.footname = userdata.footname                               # USED
        self.hairname = userdata.hairname                               # USED

        # Base stats
        self.scale = userdata.scale                                     # UNUSED
        self.baseheight = self.basestats["height"].value                # UNUSED
        self.baseweight = self.basestats["weight"].value                # UNUSED
        self.pawtoggle = userdata.pawtoggle                             # UNUSED
        self.furtoggle = userdata.furtoggle                             # UNUSED

        # What do I do with these?
        self.macrovision_model = userdata.macrovision_model             # UNUSED
        self.macrovision_view = userdata.macrovision_view               # UNUSED

        # Other stats
        self.height = self.stats["height"].value                        # USED
        self.weight = self.stats["weight"].value                        # UNUSED
        self.width = self.stats["width"].value                          # USED

        # These are like, the user settable ones?
        self.hairlength = self.stats["hairlength"].value                # UNUSED
        self.taillength = self.stats["taillength"].value                # UNUSED
        self.earheight = self.stats["earheight"].value                  # UNUSED
        self.liftstrength = self.stats["liftstrength"].value            # UNUSED
        self.footlength = self.stats["footlength"].value                # USED

        # How does this one work??
        self.shoesize = self.stats["shoesize"].value                    # UNUSED

        # TODO: Is this accounted for in the new implementation?:
        # if userdata.pawtoggle:
        #     base_footwidth = SV(base_footlength * Decimal("2/3"))   # TODO: Temp number?
        # else:
        #     base_footwidth = SV(base_footlength * Decimal("2/5"))
        # self.footwidth = SV(base_footwidth * self.scale)
        self.footwidth = self.stats["footwidth"].value                        # USED

        # OK, here's the stuff StatBox was actually made for.
        self.toeheight = self.stats["toeheight"].value                        # UNUSED
        self.shoeprintdepth = self.stats["shoeprintdepth"].value              # UNUSED
        self.pointerlength = self.stats["pointerlength"].value                # UNUSED
        self.thumbwidth = self.stats["thumbwidth"].value                      # UNUSED
        self.fingertiplength = self.stats["fingertiplength"].value            # USED
        self.fingerprintdepth = self.stats["fingerprintdepth"].value          # UNUSED
        self.threadthickness = self.stats["threadthickness"].value            # UNUSED
        self.hairwidth = self.stats["hairwidth"].value                        # UNUSED
        self.nailthickness = self.stats["nailthickness"].value                # UNUSED
        self.eyewidth = self.stats["eyewidth"].value                          # UNUSED
        self.jumpheight = self.stats["jumpheight"].value                      # UNUSED

        # Yeah, I don't think we recreated these.
        # =======================================
        self.avgheightcomp = SV(AVERAGE_HEIGHT * self.stats["viewscale"].value)        # USED
        self.avgweightcomp = WV(DEFAULT_WEIGHT * self.stats["viewscale"].value ** 3)   # UNUSED

        viewangle = calcViewAngle(self.height, average_height)
        self.avglookangle = abs(viewangle)                              # UNUSED
        self.avglookdirection = "up" if viewangle >= 0 else "down"      # UNUSED

        # base_average_ratio = self.baseheight / average_height  # TODO: Make this a property on userdata?
        # 11/26/2023: Wait, don't, do something else
        # =======================================

        # Speeds
        self.walkperhour = self.stats["walkperhour"].value                    # USED
        self.runperhour = self.stats["runperhour"].value                      # USED
        self.swimperhour = self.stats["swimperhour"].value                    # USED
        self.climbperhour = self.stats["climbperhour"].value                  # USED
        self.crawlperhour = self.stats["crawlperhour"].value                  # USED
        self.driveperhour = self.stats["driveperhour"].value                  # UNUSED
        self.spaceshipperhour = self.stats["spaceshipperhour"].value          # UNUSED

        # This got ignored in the port somehow.
        # self.spaceshipperhour = SV(average_spaceshipperhour * self.scale)

        # Step lengths
        self.walksteplength = self.stats["walksteplength"].value              # USED
        self.runsteplength = self.stats["runsteplength"].value                # UNUSED
        self.climbsteplength = self.stats["climbsteplength"].value            # UNUSED
        self.crawlsteplength = self.stats["crawlsteplength"].value            # UNUSED
        self.swimsteplength = self.stats["swimsteplength"].value              # UNUSED

        # The rest of it, I guess.
        self.horizondistance = self.stats["horizondistance"].value            # UNUSED
        self.terminalvelocity = self.stats["terminalvelocity"].value          # UNUSED
        self.fallproof = self.stats["fallproof"].value                        # UNUSED
        self.fallproofcheck = self.stats["fallprooficon"].value               # UNUSED
        self.visibility = self.stats["visibility"].value                      # UNUSED

        self.simplespeeds = self.stats["simplespeeds+"].body

    def getFormattedStat(self, key: str):
        # "foot": f"'s {self.footname.lower()} is **{self.footlength:,.3mu}** long and **{self.footwidth:,.3mu}** wide. ({self.shoesize})",
        try:
            mapped_key = statmap[key]
        except KeyError:
            return None

        returndict = {s.key: s.to_string() for s in self.stats}

        return_stat = returndict.get(mapped_key)
        return return_stat

    def __str__(self):
        return (f"<PersonStats NICKNAME = {self.stats['nickname'].values!r}, TAG = {self.tag!r}, GENDER = {self.stats['gender'].values!r}, "
                f"HEIGHT = {self.stats['height'].values!r}, BASEHEIGHT = {self.stats['baseheight'].values!r}, VIEWSCALE = {self.stats['viewscale'].values!r}, "
                f"WEIGHT = {self.stats['weight'].values!r}, BASEWEIGHT = {self.stats['baseweight'].values!r}, FOOTNAME = {self.stats['footname'].values!r}, "
                f"HAIRNAME = {self.stats['hairname'].values!r}, PAWTOGGLE = {self.stats['pawtoggle'].values!r}, FURTOGGLE = {self.stats['furtoggle'].values!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}"
                f"HAIRLENGTH = {self.stats['hairlength'].values!r}, TAILLENGTH = {self.stats['taillength'].values!r}, EARHEIGHT = {self.stats['earheight'].values!r},"
                f"LIFTSTRENGTH = {self.stats['liftstrength'].values!r}, FOOTLENGTH = {self.stats['footlength'].values!r}, "
                f"WALKPERHOUR = {self.stats['walkperhour'].values!r}, RUNPERHOUR = {self.stats['runperhour'].values!r}, VISIBILITY = {self.stats['visibility'].values!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")

        for stat in self.stats:
            if stat.is_shown:
                embed.add_field(**stat.embed)

        embed.set_footer(text=f"An average person would look {self.avgheightcomp:,.3mu}, and weigh {self.avgweightcomp:,.3mu} to you. You'd have to look {self.avglookdirection} {self.avglookangle:.0f}° to see them.")

        return embed

    def to_tag_embed(self, tag: str, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.nickname} tagged `{tag}`",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        for stat in self.stats:
            if tag in stat.tags:
                embed.add_field(**stat.embed)

        return embed


class PersonBaseStats:
    def __init__(self, userdata: User):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.gender = userdata.autogender
        self.baseheight = userdata.baseheight
        self.baseweight = userdata.baseweight
        self.height = userdata.height
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
            self.shoesize = format_shoe_size(self.footlength, self.gender)
        else:
            self.shoesize = None

        self.walkperhour = userdata.walkperhour
        self.runperhour = userdata.runperhour
        self.swimperhour = userdata.swimperhour

        self.currentscalestep = userdata.currentscalestep
        self.unitsystem = userdata.unitsystem

        self.furcheck = emojis.voteyes if userdata.furtoggle else emojis.voteno
        self.pawcheck = emojis.voteyes if userdata.pawtoggle else emojis.voteno
        self.tailcheck = emojis.voteyes if userdata.taillength else emojis.voteno

    def __str__(self):
        return (f"<PersonBaseStats NICKNAME = {self.nickname!r}, TAG = {self.tag!r}, GENDER = {self.gender!r}, "
                f"BASEHEIGHT = {self.baseheight!r}, BASEWEIGHT = {self.baseweight!r}, FOOTNAME = {self.footname!r}, "
                f"HAIRNAME = {self.hairname!r}, PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}, "
                f"HAIRLENGTH = {self.hairlength!r}, TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r}, "
                f"LIFTSTRENGTH = {self.liftstrength!r}, FOOTLENGTH = {self.footlength!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}, SWIMPERHOUR = {self.swimperhour!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Base Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        embed.add_field(name="Base Height", value=f"{self.baseheight:,.3mu}\n*{self.height / average_height:,.3} average*", inline=True)
        embed.add_field(name="Base Weight", value=f"{self.baseweight:,.3mu}\n*{self.height / average_height:,.3} average*", inline=True)
        embed.add_field(name="Unit System", value=f"{self.unitsystem.capitalize()}", inline=True)
        embed.add_field(name="Furry", value=f"**Fur: **{self.furcheck}\n**Paws: **{self.pawcheck}\n**Tail: **{self.tailcheck}\n")
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
        if self.swimperhour:
            embed.add_field(name="Swim Speed", value=f"{self.swimperhour:,.1M} per hour\n({self.swimperhour:,.1U} per hour)", inline=True)
        if self.liftstrength:
            embed.add_field(name="Lift/Carry Strength", value=f"{self.liftstrength:,.3mu}", inline=True)
        if self.macrovision_model and self.macrovision_model != "Human":
            embed.add_field(name="Macrovision Custom Model", value=f"{self.macrovision_model}, {self.macrovision_view}", inline=True)
        return embed


def format_shoe_size(footlength: SV, gender: Literal["m", "f"]):
    women = gender == "f"
    # Inch in meters
    inch = Decimal("0.0254")
    footlengthinches = footlength / inch
    shoesizeNum = (3 * (footlengthinches + Decimal("2/3"))) - 24
    prefix = ""
    if shoesizeNum < 1:
        prefix = "Children's "
        women = False
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


def fromShoeSize(shoesize: str) -> SV:
    shoesizenum = unmodifiedshoesizenum = Decimal(re.search(r"(\d*,)*\d+(\.\d*)?", shoesize)[0])
    if "w" in shoesize.lower():
        shoesizenum = unmodifiedshoesizenum - 1
    if "c" in shoesize.lower():  # Intentional override, children's sizes have no women/men distinction.
        shoesizenum = unmodifiedshoesizenum - (12 + Decimal("1/3"))
    footlengthinches = ((shoesizenum + 24) / 3) - Decimal("2/3")
    return SV.parse(f"{footlengthinches}in")


def calcViewAngle(viewer: Decimal, viewee: Decimal) -> Decimal:
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
