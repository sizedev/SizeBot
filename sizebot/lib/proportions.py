from __future__ import annotations
# from collections.abc import Callable

from copy import copy
from typing import Any, Literal, Optional, TypeVar, Union, Callable
import math
import re

from discord import Embed

from sizebot import __version__
from sizebot.lib import errors, macrovision, userdb, utils
from sizebot.lib.constants import colors, emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.freefall import terminal_velocity, AVERAGE_HUMAN_DRAG_COEFFICIENT
from sizebot.lib.units import SV, TV, WV, AV
from sizebot.lib.userdb import PlayerStats, User, DEFAULT_HEIGHT as average_height, DEFAULT_WEIGHT, DEFAULT_LIFT_STRENGTH, FALL_LIMIT, format_scale
from sizebot.lib.utils import glitch_string, minmax, pretty_time_delta, url_safe

DEFAULT_THREAD_THICKNESS = SV("0.001016")
AVERAGE_HEIGHT = average_height
AVERAGE_WALKPERHOUR = SV(5630)
AVERAGE_RUNPERHOUR = SV(10729)
AVERAGE_SWIMPERHOUR = SV(3219)
AVERAGE_CLIMBPERHOUR = SV(4828)
AVERAGE_CRAWLPERHOUR = SV(2556)
AVERAGE_DRIVEPERHOUR = SV(96561)
AVERAGE_SPACESHIPPERHOUR = SV(3600 * 1000)
WALKSTEPSPERHOUR = SV(900)
RUNSTEPSPERHOUR = SV(10200)
ONE_SOUNDSECOND = SV(340.27)
ONE_LIGHTSECOND = SV(299792000)
AVERAGE_CAL_PER_DAY = 2000
AVERAGE_WATER_PER_DAY = WV(3200)

IS_LARGE = 1.0


compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"

Formatter = Union[Callable[[Any, dict[str, Any]], str], str]


class Stat:
    def __init__(self,
                 key: str,
                 format_title: Formatter,
                 format_string: str,
                 format_embed: str,
                 userkey: Optional[str] = None,
                 default_from: Optional[Callable] = None,
                 power: Optional[int] = None,
                 requires: list[str] = None,
                 type: Optional[Callable] = None,
                 ):
        self.key = key
        self.format_title = format_title
        self.format_string = format_string
        self.format_embed = format_embed
        self.requires = requires or []
        self.power = power
        self.userkey = userkey
        self.default_from = default_from
        self.type = type

    def set(self, stats: PlayerStats, found: dict) -> StatValue:
        if any(r not in found for r in self.requires):
            return
        value = None
        if self.userkey is not None:
            value = stats[self.userkey]
        if self.default_from is not None and value is None:
            value = self.default_from(found)
        if self.type and value is not None:
            value = self.type(value)
        return StatValue(self, value)


def run_formatter(formatter: Formatter, format_dict: dict[str, Any]) -> str:
    if isinstance(formatter, str):
        return formatter.format(**format_dict)
    else:
        return formatter(format_dict)


class StatValue:
    def __init__(self, stat: Stat, value: Any):
        self.stat = stat
        self.value = value

    def scale(self, scale: Decimal, found: dict):
        # None * 2 is None
        if self.value is None:
            value = None
        elif self.stat.power is not None:
            T = type(self.value)
            value = T(self.value * (scale ** self.stat.power))
        elif self.stat.default_from:
            if any(r not in found for r in self.stat.requires):
                return
            value = self.stat.default_from(found)
        else:
            value = self.value
        if self.stat.type and value is not None:
            value = self.stat.type(value)
        return StatValue(self.stat, value)

    def to_string(self, format_dict: dict(str, str)):
        if self.value is None:
            return f"The {self.stat.format_title} stat is unavailable for this user."
        return run_formatter(self.stat.format_string, format_dict)

    def to_embed_title(self, format_dict: dict(str, str)):
        return run_formatter(self.stat.format_title, format_dict)

    def to_embed_value(self, format_dict: dict(str, str)):
        return run_formatter(self.stat.format_embed, format_dict)

    def __str__(self):
        return f"{self.stat.format_title}: {self.value}"


all_stats = {s.key: s for s in [
    Stat("height",                  "Height",                      "{nickname}'s current height is **{height:,.3mu}**, or {scale} scale.",                      "{height:,.3mu}",                                                           power=1, type=SV,        userkey="height"),
    Stat("weight",                  "Weight",                      "{nickname}'s current weight is **{weight:,.3mu}**.",                                        "{weight:,.3mu}",                                                           power=3, type=WV,        userkey="weight"),
    Stat("gender",                  "Gender",                      "{nickname}'s gender is {gender}.",                                                          "{gender}",                                                                          type=str,       userkey="gender"),
    Stat("averagescale",            "Average Scale",               "{nickname} is {averagescale} times taller than an average person.",                         "{averagescale}",                    requires=["height"],                   power=1, type=Decimal,                           default_from=lambda s: s["height"] / AVERAGE_HEIGHT),
    Stat("hairlength",              "Hair Length",                 "{nickname}'s hair is **{hairlength:,.3mu}** long.",                                         "{hairlength:,.3mu}",                                                       power=1, type=SV,        userkey="hairlength"),
    Stat("taillength",              "Tail Length",                 "{nickname}'s tail is **{taillength:,.3mu}** long.",                                         "{taillength:,.3mu}",                                                       power=1, type=SV,        userkey="taillength"),
    Stat("earheight",               "Ear Height",                  "{nickname}'s ear is **{earheight:,.3mu}** tall.",                                           "{earheight:,.3mu}",                                                        power=1, type=SV,        userkey="earheight"),
    Stat("footlength",              "Foot Length",                 "{nickname}'s foot is **{footlength:,.3mu}** long.",                                         "{footlength:,.3mu}",                requires=["height"],                   power=1, type=SV,        userkey="footlength",   default_from=lambda s: s["height"] / 7),
    Stat("liftstrength",            "Lift Strength",               "{nickname} can lift {liftstrength:,.3mu}.",                                                 "{liftstrength:,.3mu}",              requires=["height"],                   power=3, type=WV,        userkey="liftstrength", default_from=lambda s: DEFAULT_LIFT_STRENGTH),
    Stat("footwidth",               "Foot Width",                  "{nickname}'s foot is **{footwidth:,.3mu}** wide.",                                          "{footwidth:,.3mu}",                 requires=["footlength"],               power=1, type=SV,                                default_from=lambda s: s["footlength"] * Decimal(2 / 3)),
    Stat("toeheight",               "Toe Height",                  "{nickname}'s toe is **{toeheight:,.3mu}** thick.",                                          "{toeheight:,.3mu}",                 requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / 65),
    Stat("shoeprintdepth",          "Shoeprint Depth",             "{nickname}'s shoeprint is **{shoeprintdepth:,.3mu}** deep.",                                "{shoeprintdepth:,.3mu}",            requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / 135),
    Stat("pointerlength",           "Pointer Finger Length",       "{nickname}'s pointer finger is **{pointerlength:,.3mu}** long.",                            "{pointerlength:,.3mu}",             requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / Decimal(17.26)),
    Stat("thumbwidth",              "Thumb Width",                 "{nickname}'s thumb is **{thumbwidth:,.3mu}** wide.",                                        "{thumbwidth:,.3mu}",                requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / Decimal(69.06)),
    Stat("fingertiplength",         "Fingertip Length",            "{nickname}'s fingertip is **{fingertiplength:,.3mu}** long.",                               "{fingertiplength:,.3mu}",           requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / Decimal(95.95)),
    Stat("fingerprintdepth",        "Fingerprint Depth",           "{nickname}'s fingerprint is **{fingerprintdepth:,.3mu}** deep.",                            "{fingerprintdepth:,.3mu}",          requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / 35080),
    Stat("threadthickness",         "Thread Thickness",            "{nickname}'s clothing threads are **{threadthickness:,.3mu}** thick.",                      "{threadthickness:,.3mu}",                                                  power=1, type=SV,                                default_from=lambda s: DEFAULT_THREAD_THICKNESS),
    Stat("hairwidth",               "Hair Width",                  "{nickname}'s hair is **{hairwidth:,.3mu}** wide.",                                          "{hairwidth:,.3mu}",                 requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / 23387),
    Stat("nailthickness",           "Nail Thickness",              "{nickname}'s nails are **{nailthickness:,.3mu}** thick.",                                   "{nailthickness:,.3mu}",             requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / 2920),
    Stat("eyewidth",                "Eye Width",                   "{nickname}'s eyes are **{eyewidth:,.3mu}** wide.",                                          "{eyewidth:,.3mu}",                  requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / Decimal(73.083)),
    Stat("jumpheight",              "Jump Height",                 "{nickname} can jump **{jumpheight:,.3mu}** high.",                                          "{jumpheight:,.3mu}",                requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] / Decimal(3.908)),
    Stat("averagelookangle",        "Average Look Angle",          "{nickname} would have to look {averagelookangle} to see the average person.",               "{averagelookangle}",                requires=["height"],                            type=Decimal,                           default_from=lambda s: abs(calcViewAngle(s["height"], AVERAGE_HEIGHT))),
    Stat("averagelookdirection",    "Average Look Direction",      "...",                                                                                       "{averagelookdirection}",            requires=["height"],                            type=str,                               default_from=lambda s: "up" if calcViewAngle(s["height"], AVERAGE_HEIGHT) >= 0 else "down"),
    Stat("walkperhour",             "Walk Per Hour",               "{nickname} walks **{walkperhour:,.3mu} per hour**.",                                        "{walkperhour:,.3mu} per hour",      requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_WALKPERHOUR * s["averagescale"]),
    Stat("runperhour",              "Run Per Hour",                "{nickname} runs **{runperhour:,.3mu} per hour**.",                                          "{runperhour:,.3mu} per hour",       requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_RUNPERHOUR * s["averagescale"]),
    Stat("swimperhour",             "Swim Per Hour",               "{nickname} swims **{swimperhour:,.3mu} per hour**.",                                        "{swimperhour:,.3mu} per hour",      requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_SWIMPERHOUR * s["averagescale"]),
    Stat("climbperhour",            "Climb Per Hour",              "{nickname} climbs **{climbperhour:,.3mu} per hour**.",                                      "{climbperhour:,.3mu} per hour",     requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_CLIMBPERHOUR * s["averagescale"]),
    Stat("crawlperhour",            "Crawl Per Hour",              "{nickname} crawls **{crawlperhour:,.3mu} per hour**.",                                      "{crawlperhour:,.3mu} per hour",     requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_CRAWLPERHOUR * s["averagescale"]),
    Stat("driveperhour",            "Drive Per Hour",              "{nickname} drives **{driveperhour:,.3mu} per hour**.",                                      "{driveperhour:,.3mu} per hour",                                            power=1, type=SV,                                default_from=lambda s: AVERAGE_DRIVEPERHOUR),
    Stat("spaceshipperhour",        "Spaceship Per Hour",          "{nickname} flys at spaceship at **{spaceshipperhour:,.3mu} per hour**.",                     "{spaeshipperhour:,.3mu} per hour",                                         power=1, type=SV,                                default_from=lambda s: AVERAGE_SPACESHIPPERHOUR),
    Stat("walksteplength",          "Walk Step Length",            "{nickname} takes **{walksteplength:,.3mu}** strides while walking.",                        "{walksteplength:,.3mu}",            requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_WALKPERHOUR * s["averagescale"] / WALKSTEPSPERHOUR),
    Stat("runsteplength",           "Run Step Length",             "{nickname} takes **{runsteplength:,.3mu}** strides while runing.",                          "{runsteplength:,.3mu}",             requires=["averagescale"],             power=1, type=SV,                                default_from=lambda s: AVERAGE_RUNPERHOUR * s["averagescale"] / RUNSTEPSPERHOUR),
    Stat("climbsteplength",         "Climb Step Length",           "{nickname} takes **{climbsteplength:,.3mu}** strides while climbing.",                      "{climbsteplength:,.3mu}",           requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] * Decimal(1 / 2.5)),
    Stat("crawlsteplength",         "Crawl Step Length",           "{nickname} takes **{crawlsteplength:,.3mu}** strides while crawling.",                      "{crawlsteplength:,.3mu}",           requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] * Decimal(1 / 2.577)),
    Stat("swimsteplength",          "Swim Step Length",            "{nickname} takes **{swimsteplength:,.3mu}** strides while swiming.",                        "{swimsteplength:,.3mu}",            requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] * Decimal(6 / 7)),
    Stat("horizondistance",         "Distance to Horizon",         "{nickname} can see **{horizondistance:,.3mu}** to the horizon.",                            "{horizondistance:,.3mu}",           requires=["height"],                            type=SV,                                default_from=lambda s: calcHorizon(s["height"])),
    Stat("terminalvelocity",        "Terminal Velocity",           "{nickname}'s terminal velocity is **{terminalvelocity:,.3mu} per hour.**",                  "{terminalvelocity:,.3mu} per hour", requires=["weight", "averagescale"],            type=SV,                                default_from=lambda s: terminal_velocity(s["weight"], AVERAGE_HUMAN_DRAG_COEFFICIENT * s["averagescale"] ** Decimal(2))),
    Stat("fallproof",               "Fallproof",                   lambda s: f"""{s['nickname']} {'is' if s['fallproof'] else "isn't"} fallproof.""",           "{'✅' if fallproof else '❎'}",    requires=["terminalvelocity"],                  type=bool,                              default_from=lambda s: s["terminalvelocity"] < FALL_LIMIT),
    Stat("fallprooficon",           "Fallproof Icon",              lambda s: '✅' if s['fallproof'] else '❎',                                                 "{'✅' if fallproof else '❎'}",    requires=["fallproof"],                         type=str,                               default_from=lambda s: emojis.voteyes if s["fallproof"] else emojis.voteno),
    Stat("width",                   "Width",                       "{nickname} is **{width:,.3mu}** wide.",                                                     "{width:,.3mu}",                     requires=["height"],                   power=1, type=SV,                                default_from=lambda s: s["height"] * Decimal(4 / 17)),
    Stat("soundtraveltime",         "Sound Travel Time",           "It would take sound **{soundtraveltime:,.3}** to travel {nickname}'s height.",              "{soundtraveltime:,.3mu}",           requires=["height"],                   power=1, type=TV,                                default_from=lambda s: s["height"] * ONE_SOUNDSECOND),
    Stat("lighttraveltime",         "Light Travel Time",           "It would take light **{lighttraveltime:,.3}** to travel {nickname}'s height.",              "{lighttraveltime:,.3mu}",           requires=["height"],                   power=1, type=TV,                                default_from=lambda s: s["height"] * ONE_LIGHTSECOND),
    Stat("caloriesneeded",          "Calories Needed",             "{nickname} needs **{caloriesneeded:,.0d}** calories per day.",                              "{caloriesneeded:,.0d}",                                                    power=3, type=Decimal,                           default_from=lambda s: AVERAGE_CAL_PER_DAY),
    Stat("waterneeded",             "Water Needed",                "{nickname} needs **{waterneeded:,.3mu}** of water per day.",                                "{waterneeded:,.3mu}",                                                      power=3, type=WV,                                default_from=lambda s: AVERAGE_WATER_PER_DAY),
    Stat("layarea",                 "Lay Area",                    "{nickname} would cover **{layarea:,.3mu}** of area laying down.",                           "{layarea:,.3mu}",                   requires=["height", "width"],          power=2, type=AV,                                default_from=lambda s: s["height"] * s["width"]),
    Stat("footarea",                "Foot Area",                   "{nickname}'s foot would cover **{footarea:,.3mu}** of area.",                               "{footarea:,.3mu}",                  requires=["footlength", "footwidth"],  power=2, type=AV,                                default_from=lambda s: s["footlength"] * s["footwidth"]),
    Stat("fingertiparea",           "Fingertip Area",              "{nickname}'s fingertip would cover **{fingertiparea:,.3mu}** of area.",                     "{fingertiparea:,.3mu}",             requires=["fingertiplength"],          power=2, type=AV,                                default_from=lambda s: s["fingertiplength"] * s["fingertiplength"]),
    Stat("shoesize",                "Shoe Size",                   "{nickname}'s shoe size is **{shoesize}**.",                                                 "{shoesize}",                        requires=["footlength", "gender"],              type=str,                               default_from=lambda s: format_shoe_size(s["footlength"], s["gender"])),
    Stat("visibility",              "Visibility",                  "You would need **{visibility}** to see {nickname}.",                                        "{visibility}",                      requires=["height"],                            type=str,                               default_from=lambda s: calcVisibility(s["height"]))
]}


stataliases = {
    "height":           ["size"],
    "weight":           ["mass"],
    "footlength":       ["foot", "feet", "shoe", "shoes", "paw", "paws"],
    "toeheight":        ["toe", "toes"],
    "shoeprintdepth":   ["shoeprint", "footprint"],
    "pointerlength":    ["finger", "pointer"],
    "nailthickness":    ["nail", "fingernail"],
    "eyewidth":         ["eye", "eyes"],
    "hairlength":       ["hair", "fur", "furlength"],
    "hairwidth":        ["furwidth"],
    "walkperhour":      ["walk", "speed", "step"],
    "climbperhour":     ["climb", "pull"],
    "swimperhour":      ["swim", "stroke"],
    "jumpheight":       ["jump"],
    "horizondistance":  ["horizon"],
    "terminalvelocity": ["velocity", "fall"],
    "liftstrength":     ["strength", "lift", "carry", "carrystrength"],
    "visibility":       ["visible", "see"]
}
statmap = {}
for stat, aliases in stataliases.items():
    if stat not in all_stats:
        raise Exception(f"WTF MATE {stat}")
    for alias in aliases:
        statmap[alias] = stat
for stat in all_stats.keys():
    statmap[stat] = stat

# Example display code
# display_stats = [
#    DisplayStat(key="width", name="Width", statout="You're a {} wide chonker!", embedname="Width:", embedvalue="{} :widthicon:")
# ]


T = TypeVar('T', Stat, StatValue)


def process_stats(source: dict[str, T], _process: Callable[[T, dict[str, Any]], StatValue]) -> StatBox:
    queued: dict[str, T] = source.copy()
    processing: dict[str, T] = {}
    processed: dict[str, StatValue] = {}
    processed_values: dict[str, Any] = {}

    while queued:
        processing = queued
        queued = {}
        for k, s in processing.items():
            sv = _process(s, processed_values)
            if sv is None:
                # If we can't scale it, queue it for later
                queued[k] = s
            else:
                # If it's scaled, just append to the processed stats
                processed_values[k] = sv.value
                processed[k] = sv
        # If no progress
        if len(queued) == len(processing):
            raise errors.UnfoundStatException(queued.keys())
    return StatBox(processed)


class StatBox:
    def __init__(self, stats: dict[str, StatValue]):
        self.stats = stats

    @classmethod
    def process(cls, source: dict[str, T], _process: Callable[[T, dict[str, Any]], StatValue]) -> StatBox:
        queued: dict[str, T] = source.copy()
        processing: dict[str, T] = {}
        processed: dict[str, StatValue] = {}
        processed_values: dict[str, Any] = {}

        while queued:
            processing = queued
            queued = {}
            for k, s in processing.items():
                sv = _process(s, processed_values)
                if sv is None:
                    # If we can't scale it, queue it for later
                    queued[k] = s
                else:
                    # If it's scaled, just append to the processed stats
                    processed_values[k] = sv.value
                    processed[k] = sv
            # If no progress
            if len(queued) == len(processing):
                raise errors.UnfoundStatException(queued.keys())
        return cls(processed)

    @classmethod
    def load(cls, playerStats: PlayerStats) -> StatBox:
        return cls.process(all_stats, lambda s, vals: s.set(playerStats, vals))

    def scale(self, scale_value: Decimal) -> StatBox:
        return self.process(self.stats, lambda s, vals: s.scale(scale_value, vals))

    def __getitem__(self, key: str):
        return self.stats[key].value

    def __iter__(self):
        for k, sv in self.stats.items():
            yield k, sv.value


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
        embed.add_field(name=f"{emojis.comparebig} Speeds", value=self.bigToSmall.get_speeds(True), inline=False)
        embed.add_field(name=f"{emojis.comparesmall} Speeds", value=self.smallToBig.get_speeds(True), inline=False)
        embed.set_footer(text=(
            f"{self.small.nickname} would have to look {self.lookdirection} {self.lookangle:.0f}° to look at {self.big.nickname}'s face.\n"
            f"{self.big.nickname} is {self.multiplier:,.3}x taller than {self.small.nickname}.\n"
            f"{self.big.nickname} would need {self.smallToBig.visibility} to see {self.small.nickname}."))

        if self.small.incomprehensible or self.big.incomprehensible:
            ed = embed.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string("somebody once told me") + "\n" + glitch_string("the world was gonna roll me")
            embed = Embed.from_dict(ed)
            embed.set_footer(text = glitch_string(embed.footer.text))

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

        if self.small.incomprehensible or self.big.incomprehensible:
            ed = embed.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string("somebody once told me") + "\n" + glitch_string("the world was gonna roll me")
            embed = Embed.from_dict(ed)
            embed.set_footer(text = glitch_string(embed.footer.text))

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
        if self.small.incomprehensible or self.big.incomprehensible:
            return "https://cutt.ly/ik1uWDk"

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

        if self.viewer.incomprehensible or self.viewed.incomprehensible:
            walkspeedstr = glitch_string(walkspeedstr)
            runspeedstr = glitch_string(runspeedstr)
            climbspeedstr = glitch_string(climbspeedstr)
            crawlspeedstr = glitch_string(crawlspeedstr)
            swimspeedstr = glitch_string(swimspeedstr)
            drivespeedstr = glitch_string(drivespeedstr)
            reldist_print = glitch_string(reldist_print)
            shoesize = glitch_string(shoesize)

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

    def getStatEmbed(self, stat: str):
        try:
            mapped_stat = statmap[stat]
        except KeyError:
            return None

        descmap = {
            "height":           self.speedcalc(self.viewedtoviewer.height, speed = True, include_relative = True),
            "foot":             self.speedcalc(self.viewedtoviewer.footlength, speed = True, foot = True, include_relative = True),
            "toe":              self.speedcalc(self.viewedtoviewer.toeheight, speed = True, include_relative = True),
            "shoeprint":        self.speedcalc(self.viewedtoviewer.shoeprintdepth, speed = True, include_relative = True),
            "finger":           self.speedcalc(self.viewedtoviewer.pointerlength, speed = True, include_relative = True),
            "fingerprint":      self.speedcalc(self.viewedtoviewer.fingerprintdepth, speed = True, include_relative = True),
            "thumb":            self.speedcalc(self.viewedtoviewer.thumbwidth, speed = True, include_relative = True),
            "eye":              self.speedcalc(self.viewedtoviewer.eyewidth, speed = True, include_relative = True),
            "hairwidth":        self.speedcalc(self.viewedtoviewer.hairwidth, speed = True, include_relative = True),
            "hair":             self.speedcalc(self.viewedtoviewer.hairlength, speed = True, include_relative = True) if self.viewedtoviewer.hairlength is not None else None,
            "tail":             self.speedcalc(self.viewedtoviewer.taillength, speed = True, include_relative = True) if self.viewedtoviewer.taillength is not None else None,
            "ear":              self.speedcalc(self.viewedtoviewer.earheight, speed = True, include_relative = True) if self.viewedtoviewer.earheight is not None else None
        }

        if descmap[mapped_stat] is None:
            return None

        statnamemap = {
            "height":           "Height",
            "foot":             f"{self.viewed.footname} Length",
            "toe":              "Toe Height",
            "shoeprint":        "Shoeprint Depth",
            "finger":           "Finger Length",
            "thumb":            "Thumb Width",
            "fingerprint":      "Fingerprint Depth",
            "eye":              "Eye Width",
            "hairwidth":        f"{self.viewed.hairname} Width",
            "hair":             f"{self.viewed.hairname} Length",
            "tail":             "Tail Length",
            "ear":              "Ear Height",
        }

        statname = statnamemap[mapped_stat].replace("Foot", self.viewertovieweddata.footname) \
                                    .replace("Hair", self.viewertovieweddata.hairname) \
                                    .lower()

        desc = descmap[mapped_stat]

        if self.viewer.incomprehensible or self.viewed.incomprehensible:
            desc = glitch_string(desc)

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

        if self.viewer.incomprehensible or self.viewed.incomprehensible:
            ed = embed.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string(field["value"])
            embed = Embed.from_dict(ed)
            embed.set_footer(text = glitch_string(embed.footer.text))

        return embed


class PersonStats:
    def __init__(self, userdata: User):
        self.nickname = userdata.nickname
        self.tag = userdata.tag
        self.gender = userdata.autogender

        # Use the new statbox
        self.basestats = StatBox.load(userdata.stats)
        self.stats = self.basestats.scale(userdata.scale)

        # TODO: There's not a good way of getting these yet:

        self.formattedscale = format_scale(userdata.scale)
        self.viewscale = userdata.viewscale
        self.formattedweightscale = format_scale(userdata.scale, scaletype = "weight")
        self.footname = userdata.footname
        self.hairname = userdata.hairname

        # Base stats
        self.scale = userdata.scale
        self.baseheight = self.basestats["height"]
        self.baseweight = self.basestats["weight"]
        self.pawtoggle = userdata.pawtoggle
        self.furtoggle = userdata.furtoggle

        # What do I do with these?
        self.incomprehensible = userdata.incomprehensible
        self.macrovision_model = userdata.macrovision_model
        self.macrovision_view = userdata.macrovision_view

        # Other stats
        self.height = self.stats["height"]
        self.weight = self.stats["weight"]
        self.width = self.stats["width"]

        # These are like, the user settable ones?
        self.hairlength = self.stats["hairlength"]
        self.taillength = self.stats["taillength"]
        self.earheight = self.stats["earheight"]
        self.liftstrength = self.stats["liftstrength"]
        self.footlength = self.stats["footlength"]

        # How does this one work??
        self.shoesize = format_shoe_size(self.footlength, self.gender)

        # TODO: Is this accounted for in the new implementation?:
        # if userdata.pawtoggle:
        #     base_footwidth = SV(base_footlength * Decimal("2/3"))   # TODO: Temp number?
        # else:
        #     base_footwidth = SV(base_footlength * Decimal("2/5"))
        # self.footwidth = SV(base_footwidth * self.scale)
        self.footwidth = self.stats["footwidth"]

        # OK, here's the stuff StatBox was actually made for.
        self.toeheight = self.stats["toeheight"]
        self.shoeprintdepth = self.stats["shoeprintdepth"]
        self.pointerlength = self.stats["pointerlength"]
        self.thumbwidth = self.stats["thumbwidth"]
        self.fingertiplength = self.stats["fingertiplength"]
        self.fingerprintdepth = self.stats["fingerprintdepth"]
        self.threadthickness = self.stats["threadthickness"]
        self.hairwidth = self.stats["hairwidth"]
        self.nailthickness = self.stats["nailthickness"]
        self.eyewidth = self.stats["eyewidth"]
        self.jumpheight = self.stats["jumpheight"]

        # Yeah, I don't think we recreated these.
        # =======================================
        self.avgheightcomp = SV(AVERAGE_HEIGHT * self.viewscale)
        self.avgweightcomp = WV(DEFAULT_WEIGHT * self.viewscale ** 3)

        viewangle = calcViewAngle(self.height, average_height)
        self.avglookangle = abs(viewangle)
        self.avglookdirection = "up" if viewangle >= 0 else "down"

        # base_average_ratio = self.baseheight / average_height  # TODO: Make this a property on userdata?
        # 11/26/2023: Wait, don't, do something else
        # =======================================

        # Speeds
        self.walkperhour = self.stats["walkperhour"]
        self.runperhour = self.stats["runperhour"]
        self.swimperhour = self.stats["swimperhour"]
        self.climbperhour = self.stats["climbperhour"]
        self.crawlperhour = self.stats["crawlperhour"]
        self.driveperhour = self.stats["driveperhour"]
        self.spaceshipperhour = self.stats["spaceshipperhour"]

        # This got ignored in the port somehow.
        # self.spaceshipperhour = SV(average_spaceshipperhour * self.scale)

        # Step lengths
        self.walksteplength = self.stats["walksteplength"]
        self.runsteplength = self.stats["runsteplength"]
        self.climbsteplength = self.stats["climbsteplength"]
        self.crawlsteplength = self.stats["crawlsteplength"]
        self.swimsteplength = self.stats["swimsteplength"]

        # The rest of it, I guess.
        self.horizondistance = self.stats["horizondistance"]
        self.terminalvelocity = self.stats["terminalvelocity"]
        self.fallproof = self.stats["fallproof"]
        self.fallproofcheck = self.stats["fallprooficon"]
        self.visibility = self.stats["visibility"]

    def getFormattedStat(self, stat: str):
        # "foot": f"'s {self.footname.lower()} is **{self.footlength:,.3mu}** long and **{self.footwidth:,.3mu}** wide. ({self.shoesize})",
        try:
            mapped_stat = statmap[stat]
        except KeyError:
            return None

        format_dict = dict(self.stats) | {"nickname": self.nickname, "scale": format_scale(self.scale)}
        returndict = {k: sv.to_string(format_dict) for k, sv in self.stats.stats.items()}

        if self.incomprehensible:
            return glitch_string(returndict.get(stat))
        return returndict.get(mapped_stat)

    def get_speeds(self, simple = False):
        if simple:
            return (f"{emojis.walk} {self.walkperhour:,.1M} per hour / {self.walkperhour:,.1U} per hour\n"
                    f"{emojis.run} {self.runperhour:,.1M} per hour / {self.runperhour:,.1U} per hour\n"
                    f"{emojis.climb} {self.climbperhour:,.1M} per hour / {self.climbperhour:,.1U} per hour\n"
                    f"{emojis.swim} {self.swimperhour:,.1M} per hour / {self.swimperhour:,.1U} per hour")

        return (f"{emojis.walk} {self.walkperhour:,.1M} per hour / {self.walkperhour:,.1U} per hour\n"
                f"{emojis.run} {self.runperhour:,.1M} per hour / {self.runperhour:,.1U} per hour\n"
                f"{emojis.climb} {self.climbperhour:,.1M} per hour / {self.climbperhour:,.1U} per hour\n"
                f"{emojis.crawl} {self.crawlperhour:,.1M} per hour / {self.crawlperhour:,.1U} per hour\n"
                f"{emojis.swim} {self.swimperhour:,.1M} per hour / {self.swimperhour:,.1U} per hour\n"
                f"{emojis.drive} {self.driveperhour:,.1M} per hour / {self.driveperhour:,.1U} per hour\n"
                f"{emojis.spaceship} {self.spaceshipperhour:,.1M} per hour / {self.spaceshipperhour:,.1U} per hour")

    def __str__(self):
        return (f"<PersonStats NICKNAME = {self.nickname!r}, TAG = {self.tag!r}, GENDER = {self.gender!r}, "
                f"HEIGHT = {self.height!r}, BASEHEIGHT = {self.baseheight!r}, VIEWSCALE = {self.viewscale!r}, "
                f"WEIGHT = {self.weight!r}, BASEWEIGHT = {self.baseweight!r}, FOOTNAME = {self.footname!r}, "
                f"HAIRNAME = {self.hairname!r}, PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}"
                f"HAIRLENGTH = {self.hairlength!r}, TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r},"
                f"LIFTSTRENGTH = {self.liftstrength!r}, FOOTLENGTH = {self.footlength!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}, VISIBILITY = {self.visibility!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        heightstring = f"{self.height:,.3mu}\n*{self.formattedscale} scale*"
        if self.height < SV(1):
            heightstring += f"\n*{self.nickname} would need {self.visibility} to be seen.*"
        embed.add_field(name="Current Height", value=heightstring, inline=True)
        embed.add_field(name="Current Weight", value=f"{self.weight:,.3mu}\n*{self.formattedweightscale} scale*", inline=True)
        embed.add_field(name=f"{self.footname} Length", value=f"{self.footlength:.3mu}\n({self.shoesize})", inline=True)
        embed.add_field(name=f"{self.footname} Width", value=format(self.footwidth, ",.3mu"), inline=True)
        embed.add_field(name="Shoeprint Depth", value=format(self.shoeprintdepth, ",.3mu"), inline=True)
        embed.add_field(name="Pointer Finger Length", value=format(self.pointerlength, ",.3mu"), inline=True)
        if self.scale > IS_LARGE:
            embed.add_field(name="Toe Height", value=format(self.toeheight, ",.3mu"), inline=True)
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
        if self.scale > IS_LARGE:
            embed.add_field(name=f"{self.hairname} Width", value=format(self.hairwidth, ",.3mu"), inline=True)
            embed.add_field(name="Eye Width", value=format(self.eyewidth, ",.3mu"), inline=True)
        embed.add_field(name="Jump Height", value=f"{self.jumpheight:,.3mu}", inline=True)
        embed.add_field(name="View Distance to Horizon", value=f"{self.horizondistance:,.3mu}", inline=True)
        if self.fallproof:
            embed.add_field(name="Terminal Velocity", value = f"{self.terminalvelocity:,.1M} per second\n({self.terminalvelocity:,.1U} per second)\n*This user can safely fall from any height.*", inline = True)
        else:
            embed.add_field(name="Terminal Velocity", value = f"{self.terminalvelocity:,.1M} per second\n({self.terminalvelocity:,.1U} per second)", inline = True)
        embed.add_field(name="Lift/Carry Strength", value=f"{self.liftstrength:,.3mu}", inline=True)
        embed.add_field(name="Speeds", value=self.get_speeds(), inline=False)
        embed.add_field(name="Character Bases", value=f"{self.baseheight:,.3mu} | {self.baseweight:,.3mu}", inline=False)
        embed.set_footer(text=f"An average person would look {self.avgheightcomp:,.3mu}, and weigh {self.avgweightcomp:,.3mu} to you. You'd have to look {self.avglookdirection} {self.avglookangle:.0f}° to see them.")

        if self.incomprehensible:
            ed = embed.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string(field["value"])
            embed = Embed.from_dict(ed)
            embed.set_footer(text = glitch_string(embed.footer.text))

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


def calcHorizon(height: SV) -> SV:
    EARTH_RADIUS = 6378137
    return SV(math.sqrt((EARTH_RADIUS + height) ** 2 - EARTH_RADIUS ** 2))


def calcVisibility(height: SV) -> str:
    if height < SV(0.000001):
        visibility = "magic"
    elif height < SV(0.00005):
        visibility = "a microscope"
    elif height < SV(0.00025):
        visibility = "a magnifying glass"
    else:
        visibility = "only the naked eye"
    return visibility
