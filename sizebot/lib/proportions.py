from __future__ import annotations

from copy import copy
import logging
import math

from discord import Embed

from sizebot import __version__
from sizebot.lib import errors, macrovision, userdb, utils
from sizebot.lib.constants import colors, emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.speed import speedcalc
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import User, DEFAULT_HEIGHT as average_height, DEFAULT_WEIGHT
from sizebot.lib.utils import minmax, url_safe
from sizebot.lib.stats import statmap, StatBox

AVERAGE_HEIGHT = average_height
AVERAGE_WALKPERHOUR = SV(5630)

logger = logging.getLogger("sizebot")


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

    def get_single_body(self, key: str) -> str:
        try:
            mapped_key = statmap[key]
        except KeyError:
            return None

        bigstat = self.bigToSmall.stats[mapped_key]
        smallstat = self.smallToBig.stats[mapped_key]

        bigstattext = bigstat.body if bigstat.value is not None else f"{self.big.nickname} doesn't have that stat."
        smallstattext = smallstat.body if smallstat.value is not None else f"{self.small.nickname} doesn't have that stat."

        return_stat = (f"{emojis.comparebig}{bigstattext}\n"
                       f"{emojis.comparesmall}{smallstattext}")

        return return_stat

    def getFormattedStat(self, key: str):
        body = self.get_single_body(key)
        if body is None:
            return None
        
        return f"Comparing `{key}` between {emojis.comparebigcenter}**{self.big.nickname}** and **{emojis.comparesmallcenter}{self.small.nickname}**:\n" + body

    def __repr__(self):
        return f"<PersonComparison SMALL = {self.small.nickname}, BIG = {self.big.nickname}>"

    def __str__(self):
        return repr(self)

    # TODO: CamelCase
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
        embed.add_field(value=(
            f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{self.big.nickname}** looks to {emojis.comparesmallcenter} **{self.small.nickname}**.\n"
            f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{self.small.nickname}** looks to {emojis.comparebigcenter} **{self.big.nickname}**."), inline=False)
        

        for sstat, bstat in zip(self.smallToBig.stats, self.bigToSmall.stats):
            if (sstat.is_shown or bstat.is_shown) and (sstat.value is not None or bstat.value is not None):
                logger.info(f"{sstat.key}, {bstat.key}: {sstat.value}, {bstat.value}")
                embed.add_field(name = sstat.title, value = self.get_single_body(sstat.key), inline = True)

        embed.add_field(name=f"{emojis.comparebig} Speeds", value=self.bigToSmall.simplespeeds, inline=False)
        embed.add_field(name=f"{emojis.comparesmall} Speeds", value=self.smallToBig.simplespeeds, inline=False)
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}.\n"
            f"{self.big.nickname} would need {self.smallToBig.visibility} to see {self.small.nickname}."))

        return embed

    # TODO: CamelCase
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

        # Use the new statbox
        self.viewer = StatBox.load(self._viewer.stats).scale(self._viewer.scale)
        self.viewed = StatBox.load(self._viewed.stats).scale(self._viewed.scale)

        if self.viewer["height"].value == 0 and self.viewed["height"].value == 0:
            self.multiplier = Decimal(1)
        else:
            self.multiplier = self.viewed["height"].value / self.viewer["height"].value

        self.footlabel = "Paw" if self.viewed["pawtoggle"].value else "Foot"
        self.hairlabel = "Fur" if self.viewed["furtoggle"].value else "Hair"

        viewangle = calcViewAngle(self.viewer["height"].value, self.viewed["height"].value)
        self.lookangle = abs(viewangle)
        self.lookdirection = "up" if viewangle >= 0 else "down"

    def __str__(self):
        return f"<PersonSpeedComparison VIEWER = {self.viewer!r}, VIEWED = {self.viewed!r}, \
            VIEWERTOVIEWED = {self.viewer!r}, VIEWEDTOVIEWER = {self.viewed!r}>"

    def __repr__(self):
        return str(self)

    # TODO: CamelCase
    def getStatEmbed(self, key: str):
        try:
            mapped_key = statmap[key]
        except KeyError:
            return None

        stat = self.viewed[mapped_key]

        if stat.value is None:
            return None
        elif not isinstance(stat.value, SV):
            return None

        return Embed(
            title = f"To move the distance of {self.viewed["nickname"].value}'s {stat.title.lower()}, it would take {self.viewer["nickname"].value}...",
            description = speedcalc(self.viewer, stat.value, speed = True, include_relative = True, foot = mapped_key == "footlength"))

    # TODO: CamelCase
    async def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(
            title=f"Speed/Distance Comparison of {self.viewed["nickname"].value} and {self.viewer["nickname"].value}",
            description=f"*Requested by {requestertag}*",
            color=colors.purple
        )
        embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
        embed.add_field(name=f"**{self.viewer["nickname"].value}** Speeds", value=(
            f"{emojis.walk} **Walk Speed:** {self.viewer["walkperhour"].value:,.3mu} per hour\n"
            f"{emojis.run} **Run Speed:** {self.viewer["runperhour"].value:,.3mu} per hour\n"
            f"{emojis.climb} **Climb Speed:** {self.viewer["climbperhour"].value:,.3mu} per hour\n"
            f"{emojis.crawl} **Crawl Speed:** {self.viewer["crawlperhour"].value:,.3mu} per hour\n"
            f"{emojis.swim} **Swim Speed:** {self.viewer["swimperhour"].value:,.3mu} per hour"), inline=False)
        embed.add_field(name="Height", value=(speedcalc(self.viewer, self.viewed["height"].value)), inline=True)
        embed.add_field(name=f"{self.footlabel} Length", value=(speedcalc(self.viewer, self.viewed["footlength"].value, foot = True)), inline=True)
        embed.add_field(name=f"{self.footlabel} Width", value=(speedcalc(self.viewer, self.viewed["footwidth"].value)), inline=True)
        embed.add_field(name="Toe Height", value=(speedcalc(self.viewer, self.viewed["toeheight"].value)), inline=True)
        embed.add_field(name="Shoeprint Depth", value=(speedcalc(self.viewer, self.viewed["shoeprintdepth"].value)), inline=True)
        embed.add_field(name="Pointer Finger Length", value=(speedcalc(self.viewer, self.viewed["pointerlength"].value)), inline=True)
        embed.add_field(name="Thumb Width", value=(speedcalc(self.viewer, self.viewed["thumbwidth"].value)), inline=True)
        embed.add_field(name="Nail Thickness", value=(speedcalc(self.viewer, self.viewed["nailthickness"].value)), inline=True)
        embed.add_field(name="Fingerprint Depth", value=(speedcalc(self.viewer, self.viewed["fingerprintdepth"].value)), inline=True)
        if self.viewed["hairlength"].value:
            embed.add_field(name=f"{self.hairlabel} Length", value=(speedcalc(self.viewed["hairlength"].value)), inline=True)
        if self.viewed["taillength"].value:
            embed.add_field(name="Tail Length", value=(speedcalc(self.viewer, self.viewed["taillength"].value)), inline=True)
        if self.viewed["earheight"].value:
            embed.add_field(name="Ear Height", value=(speedcalc(self.viewer, self.viewed["earheight"].value)), inline=True)
        embed.add_field(name=f"{self.hairlabel} Width", value=(speedcalc(self.viewer, self.viewed["hairwidth"].value)), inline=True)
        embed.add_field(name="Eye Width", value=(speedcalc(self.viewer, self.viewed["eyewidth"].value)), inline=True)
        embed.set_footer(text=(f"{self.viewed["nickname"].value} is {self.multiplier:,.3}x taller than {self.viewer["nickname"].value}."))

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

    # TODO: CamelCase
    def getFormattedStat(self, key: str) -> str:
        # "foot": f"'s {self.footname.lower()} is **{self.footlength:,.3mu}** long and **{self.footwidth:,.3mu}** wide. ({self.shoesize})",
        try:
            mapped_key = statmap[key]
        except KeyError:
            return None

        returndict = {s.key: s.string for s in self.stats}

        return_stat = returndict.get(mapped_key)
        return return_stat

    def __repr__(self):
        return (f"<PersonStats NICKNAME = {self.stats['nickname'].values!r}>")

    def __str__(self):
        return repr(self)

    # TODO: CamelCase
    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.stats['nickname'].value}",
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


def get_basestats_embed(userdata: User, requesterID = None):
    basestats = StatBox.load(userdata.stats)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=f"Base Stats for {basestats['nickname'].value}",
                  description=f"*Requested by {requestertag}*",
                  color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in basestats:
        if stat.is_shown:
            embed.add_field(**stat.embed)

    # REMOVED: unitsystem, furcheck, pawcheck, tailcheck, macrovision_model, macrovision_view
    return embed


def get_settings_embed(userdata: User, requesterID = None):
    basestats = StatBox.load(userdata.stats)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=f"Settings for {basestats['nickname'].value}",
                  description=f"*Requested by {requestertag}*",
                  color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in basestats:
        if stat.definition.userkey is not None:
            if stat.is_setbyuser:
                embed.add_field(**stat.embed)
            else:
                embed.add_field(
                    name=stat.title,
                    value="**NOT SET**",
                    inline=stat.definition.inline
                )

    return embed


# TODO: CamelCase
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
