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
from sizebot.lib.userdb import PlayerStats, User, DEFAULT_HEIGHT as average_height, DEFAULT_WEIGHT, DEFAULT_LIFT_STRENGTH, FALL_LIMIT
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
IS_VERY_LARGE = 10.0


def format_scale(scale: Decimal):
    reversescale = 1 / scale

    if reversescale > 10:
        dec = 0
    elif reversescale > 1:
        dec = 1
    else:
        return f"{scale:,.3}x"

    return f"{scale:,.3}x (1:{reversescale:,.{dec}})"


compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"

Formatter = Union[Callable[[Any, dict[str, Any]], str], str]


class Stat:
    def __init__(self,
                 key: str,
                 format_title: Formatter,
                 format_string: Formatter,
                 format_embed: Formatter,
                 is_shown: Union[Callable[[dict[str, any]], bool], bool] = lambda s: True,
                 userkey: Optional[str] = None,
                 default_from: Optional[Callable] = None,
                 power: Optional[int] = None,
                 requires: list[str] = None,
                 type: Optional[Callable] = None,
                 z: Optional[int] = None,
                 tags: list[str] = None
                 ):
        self.key = key
        self.format_title = format_title
        self.format_string = format_string
        self.format_embed = format_embed
        self.is_shown = (lambda s: is_shown) if isinstance(is_shown, bool) else is_shown
        self.requires = requires or []
        self.power = power
        self.userkey = userkey
        self.default_from = default_from
        self.type = type
        self.z = z
        self.tags = tags or []

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


def run_statbox_formatter(formatter: Formatter, statbox: StatBox) -> str:
    if isinstance(formatter, str):
        return formatter
    else:
        return formatter(statbox)


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

    def to_string(self, format_dict: dict[str, str]):
        if self.value is None:
            return f"The {self.stat.format_title} stat is unavailable for this user."
        return run_formatter(self.stat.format_string, format_dict)

    def is_shown(self, value_dict: dict[str, any]) -> bool:
        return self.stat.is_shown(value_dict)

    def to_embed_title(self, format_dict: dict[str, str]):
        return run_formatter(self.stat.format_title, format_dict)

    def to_embed_value(self, format_dict: dict[str, str]):
        return run_formatter(self.stat.format_embed, format_dict)

    def __str__(self):
        return f"{self.stat.format_title}: {self.value}"


CHK_Y = "✅"
CHK_N = "❎"

all_stats = {s.key: s for s in [
    Stat("nickname",                "Nickname",                 "{nickname}",                                                                       "{nickname}",                                           is_shown=False,                                                                                     type=str,       userkey="nickname"),
    Stat("scale",                   "Scale",                    lambda s: format_scale(s['scale']),                                                 lambda s: format_scale(s['scale']),                                                                                                             power=1,    type=Decimal,   userkey="scale"),
    Stat("viewscale",               "Viewscale",                lambda s: format_scale(s['viewscale']),                                             lambda s: format_scale(s['viewscale']),                 is_shown=False,                                 requires=["scale"],                                 type=Decimal,                           default_from=lambda s: 1 / s["scale"]),
    Stat("squarescale",             "Square Scale",             lambda s: format_scale(s['squarescale']),                                           lambda s: format_scale(s['squarescale']),               is_shown=False,                                 requires=["scale"],                     power=2,    type=Decimal,                           default_from=lambda s: s["scale"] ** 2),
    Stat("cubescale",               "Cube Scale",               lambda s: format_scale(s['cubescale']),                                             lambda s: format_scale(s['cubescale']),                 is_shown=False,                                 requires=["scale"],                     power=3,    type=Decimal,                           default_from=lambda s: s["scale"] ** 3),
    Stat("height",                  "Height",                   "{nickname}'s current height is **{height:,.3mu}**, or {scale} scale.",             "{height:,.3mu}",                                                                                                                               power=1,    type=SV,        userkey="height", tags = ["height"]),
    Stat("weight",                  "Weight",                   "{nickname}'s current weight is **{weight:,.3mu}**.",                               "{weight:,.3mu}",                                                                                                                               power=3,    type=WV,        userkey="weight"),
    Stat("gender",                  "Gender",                   "{nickname}'s gender is {gender}.",                                                 "{gender}",                                             is_shown=False,                                                                                     type=str,       userkey="gender"),  # TODO: Should this be autogender?
    Stat("averagescale",            "Average Scale",            "{nickname} is {averagescale} times taller than an average person.",                "{averagescale}",                                       is_shown=False,                                 requires=["height"],                    power=1,    type=Decimal,                           default_from=lambda s: s["height"] / AVERAGE_HEIGHT),
    Stat("hairlength",              "Hair Length",              "{nickname}'s hair is **{hairlength:,.3mu}** long.",                                "{hairlength:,.3mu}",                                   is_shown=lambda s: s["hairlength"],                                                     power=1,    type=SV,        userkey="hairlength"),
    Stat("taillength",              "Tail Length",              "{nickname}'s tail is **{taillength:,.3mu}** long.",                                "{taillength:,.3mu}",                                   is_shown=lambda s: s["taillength"],                                                     power=1,    type=SV,        userkey="taillength", tags = ["furry"]),
    Stat("earheight",               "Ear Height",               "{nickname}'s ear is **{earheight:,.3mu}** tall.",                                  "{earheight:,.3mu}",                                    is_shown=lambda s: s["earheight"],                                                      power=1,    type=SV,        userkey="earheight", tags = ["furry"]),
    Stat("footlength",              "Foot Length",              "{nickname}'s foot is **{footlength:,.3mu}** long.",                                "{footlength:,.3mu}",                                   is_shown=False,                                 requires=["height"],                    power=1,    type=SV,        userkey="footlength",   default_from=lambda s: s["height"] / 7, tags = ["foot"]),
    Stat("liftstrength",            "Lift Strength",            "{nickname} can lift {liftstrength:,.3mu}.",                                        "{liftstrength:,.3mu}",                                                                                 requires=["height"],                    power=3,    type=WV,        userkey="liftstrength", default_from=lambda s: DEFAULT_LIFT_STRENGTH),
    Stat("footwidth",               "Foot Width",               "{nickname}'s foot is **{footwidth:,.3mu}** wide.",                                 "{footwidth:,.3mu}",                                                                                    requires=["footlength"],                power=1,    type=SV,                                default_from=(lambda s: s["footlength"] * Decimal(2 / 3)), tags = ["foot"]),
    Stat("toeheight",               "Toe Height",               "{nickname}'s toe is **{toeheight:,.3mu}** thick.",                                 "{toeheight:,.3mu}",                                    is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / 65), tags = ["height"]),
    Stat("shoeprintdepth",          "Shoeprint Depth",          "{nickname}'s shoeprint is **{shoeprintdepth:,.3mu}** deep.",                       "{shoeprintdepth:,.3mu}",                               is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                default_from=lambda s: s["height"] / 135),
    Stat("pointerlength",           "Pointer Finger Length",    "{nickname}'s pointer finger is **{pointerlength:,.3mu}** long.",                   "{pointerlength:,.3mu}",                                                                                requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / Decimal(17.26)), tags = ["hand"]),
    Stat("thumbwidth",              "Thumb Width",              "{nickname}'s thumb is **{thumbwidth:,.3mu}** wide.",                               "{thumbwidth:,.3mu}",                                   is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / Decimal(69.06)), tags = ["hand"]),
    Stat("fingertiplength",         "Fingertip Length",         "{nickname}'s fingertip is **{fingertiplength:,.3mu}** long.",                      "{fingertiplength:,.3mu}",                              is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / Decimal(95.95)), tags = ["hand"]),
    Stat("fingerprintdepth",        "Fingerprint Depth",        "{nickname}'s fingerprint is **{fingerprintdepth:,.3mu}** deep.",                   "{fingerprintdepth:,.3mu}",                             is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / 35080), tags = ["hand"]),
    Stat("threadthickness",         "Thread Thickness",         "{nickname}'s clothing threads are **{threadthickness:,.3mu}** thick.",             "{threadthickness:,.3mu}",                              is_shown=lambda s: s["scale"] > IS_LARGE,                                               power=1,    type=SV,                                default_from=lambda s: DEFAULT_THREAD_THICKNESS),
    Stat("hairwidth",               "Hair Width",               "{nickname}'s hair is **{hairwidth:,.3mu}** wide.",                                 "{hairwidth:,.3mu}",                                    is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                default_from=lambda s: s["height"] / 23387),
    Stat("nailthickness",           "Nail Thickness",           "{nickname}'s nails are **{nailthickness:,.3mu}** thick.",                          "{nailthickness:,.3mu}",                                is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] / 2920), tags = ["hand"]),
    Stat("eyewidth",                "Eye Width",                "{nickname}'s eyes are **{eyewidth:,.3mu}** wide.",                                 "{eyewidth:,.3mu}",                                     is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                default_from=lambda s: s["height"] / Decimal(73.083)),
    Stat("jumpheight",              "Jump Height",              "{nickname} can jump **{jumpheight:,.3mu}** high.",                                 "{jumpheight:,.3mu}",                                                                                   requires=["height"],                    power=1,    type=SV,                                default_from=lambda s: s["height"] / Decimal(3.908)),
    Stat("averagelookangle",        "Average Look Angle",       "{nickname} would have to look {averagelookangle} to see the average person.",      "{averagelookangle}",                                                                                   is_shown=False,                         requires=["height"],                                type=Decimal,                           default_from=lambda s: abs(calcViewAngle(s["height"], AVERAGE_HEIGHT))),
    Stat("averagelookdirection",    "Average Look Direction",   "...",                                                                              "{averagelookdirection}",                                                                               is_shown=False,                         requires=["height"],                                type=str,                               default_from=lambda s: "up" if calcViewAngle(s["height"], AVERAGE_HEIGHT) >= 0 else "down"),
    Stat("walkperhour",             "Walk Per Hour",            "{nickname} walks **{walkperhour:,.3mu} per hour**.",                               emojis.walk + "{walkperhour:,.1M} per hour / {walkperhour:,.1U} per hour",                              is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_WALKPERHOUR * s["averagescale"]), tags = ["movement"]),
    Stat("runperhour",              "Run Per Hour",             "{nickname} runs **{runperhour:,.3mu} per hour**.",                                 emojis.run + " {runperhour:,.1M} per hour / {runperhour:,.1U} per hour",                                is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_RUNPERHOUR * s["averagescale"]), tags = ["movement"]),
    Stat("swimperhour",             "Swim Per Hour",            "{nickname} swims **{swimperhour:,.3mu} per hour**.",                               emojis.climb + " {swimperhour:,.1M} per hour / {swimperhour:,.1U} per hour",                            is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_SWIMPERHOUR * s["averagescale"]), tags = ["movement"]),
    Stat("climbperhour",            "Climb Per Hour",           "{nickname} climbs **{climbperhour:,.3mu} per hour**.",                             emojis.crawl + " {climbperhour:,.1M} per hour / {climbperhour:,.1U} per hour",                          is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_CLIMBPERHOUR * s["averagescale"]), tags = ["movement"]),
    Stat("crawlperhour",            "Crawl Per Hour",           "{nickname} crawls **{crawlperhour:,.3mu} per hour**.",                             emojis.swim + " {crawlperhour:,.1M} per hour / {crawlperhour:,.1U} per hour",                           is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_CRAWLPERHOUR * s["averagescale"]), tags = ["movement"]),
    Stat("driveperhour",            "Drive Per Hour",           "{nickname} drives **{driveperhour:,.3mu} per hour**.",                             emojis.drive + " {driveperhour:,.1M} per hour / {driveperhour:,.1U} per hour",                          is_shown=False,                                                                 power=1,    type=SV,                                default_from=(lambda s: AVERAGE_DRIVEPERHOUR), tags = ["movement"]),
    Stat("spaceshipperhour",        "Spaceship Per Hour",       "{nickname} flys at spaceship at **{spaceshipperhour:,.3mu} per hour**.",           emojis.spaceship + " {spaceshipperhour:,.1M} per hour / {spaceshipperhour:,.1U} per hour",              is_shown=False,                                                                 power=1,    type=SV,                                default_from=(lambda s: AVERAGE_SPACESHIPPERHOUR), tags = ["movement"]),
    Stat("walksteplength",          "Walk Step Length",         "{nickname} takes **{walksteplength:,.3mu}** strides while walking.",               "{walksteplength:,.3mu}",                                                                               is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_WALKPERHOUR * s["averagescale"] / WALKSTEPSPERHOUR), tags = ["movement"]),
    Stat("runsteplength",           "Run Step Length",          "{nickname} takes **{runsteplength:,.3mu}** strides while runing.",                 "{runsteplength:,.3mu}",                                                                                is_shown=False,                         requires=["averagescale"],              power=1,    type=SV,                                default_from=(lambda s: AVERAGE_RUNPERHOUR * s["averagescale"] / RUNSTEPSPERHOUR), tags = ["movement"]),
    Stat("climbsteplength",         "Climb Step Length",        "{nickname} takes **{climbsteplength:,.3mu}** strides while climbing.",             "{climbsteplength:,.3mu}",                                                                              is_shown=False,                         requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] * Decimal(1 / 2.5)), tags = ["movement"]),
    Stat("crawlsteplength",         "Crawl Step Length",        "{nickname} takes **{crawlsteplength:,.3mu}** strides while crawling.",             "{crawlsteplength:,.3mu}",                                                                              is_shown=False,                         requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] * Decimal(1 / 2.577)), tags = ["movement"]),
    Stat("swimsteplength",          "Swim Step Length",         "{nickname} takes **{swimsteplength:,.3mu}** strides while swiming.",               "{swimsteplength:,.3mu}",                                                                               is_shown=False,                         requires=["height"],                    power=1,    type=SV,                                default_from=(lambda s: s["height"] * Decimal(6 / 7)), tags = ["movement"]),
    Stat("horizondistance",         "View Distance to Horizon", "{nickname} can see **{horizondistance:,.3mu}** to the horizon.",                   "{horizondistance:,.3mu}",                                                                              is_shown=False,                         requires=["height"],                                type=SV,                                default_from=lambda s: calcHorizon(s["height"])),
    Stat("terminalvelocity",        "Terminal Velocity",        "{nickname}'s terminal velocity is **{terminalvelocity:,.3mu} per hour.**",         lambda s: f"{s['terminalvelocity']:,.1M} per second\n({s['terminalvelocity']:,.1U} per second)" + ("\n*This user can safely fall from any height.*" if s["fallproof"] else ""),                     requires=["weight", "averagescale"],    type=SV, default_from=lambda s: terminal_velocity(s["weight"], AVERAGE_HUMAN_DRAG_COEFFICIENT * s["averagescale"] ** Decimal(2))),
    Stat("fallproof",               "Fallproof",                lambda s: f"""{s['nickname']} {'is' if s['fallproof'] else "isn't"} fallproof.""",  lambda s: CHK_Y if s['fallproof'] else CHK_N,                                                           is_shown=False,                         requires=["terminalvelocity"],                      type=bool,                              default_from=lambda s: s["terminalvelocity"] < FALL_LIMIT),
    Stat("fallprooficon",           "Fallproof Icon",           lambda s: CHK_Y if s['fallproof'] else CHK_N,                                       lambda s: CHK_Y if s['fallproof'] else CHK_N,                                                           is_shown=False,                         requires=["fallproof"],                             type=str,                               default_from=lambda s: emojis.voteyes if s["fallproof"] else emojis.voteno),
    Stat("width",                   "Width",                    "{nickname} is **{width:,.3mu}** wide.",                                            "{width:,.3mu}",                                        is_shown=False,                                 requires=["height"],                    power=1,    type=SV,                                default_from=lambda s: s["height"] * Decimal(4 / 17)),
    Stat("soundtraveltime",         "Sound Travel Time",        "It would take sound **{soundtraveltime:,.3}** to travel {nickname}'s height.",     "{soundtraveltime:,.3mu}",                              is_shown=False,                                 requires=["height"],                    power=1,    type=TV,                                default_from=lambda s: s["height"] * ONE_SOUNDSECOND),
    Stat("lighttraveltime",         "Light Travel Time",        "It would take light **{lighttraveltime:,.3}** to travel {nickname}'s height.",     "{lighttraveltime:,.3mu}",                              is_shown=False,                                 requires=["height"],                    power=1,    type=TV,                                default_from=lambda s: s["height"] * ONE_LIGHTSECOND),
    Stat("caloriesneeded",          "Calories Needed",          "{nickname} needs **{caloriesneeded:,.0d}** calories per day.",                     "{caloriesneeded:,.0d}",                                is_shown=False,                                                                         power=3,    type=Decimal,                           default_from=lambda s: AVERAGE_CAL_PER_DAY),
    Stat("waterneeded",             "Water Needed",             "{nickname} needs **{waterneeded:,.3mu}** of water per day.",                       "{waterneeded:,.3mu}",                                  is_shown=False,                                                                         power=3,    type=WV,                                default_from=lambda s: AVERAGE_WATER_PER_DAY),
    Stat("layarea",                 "Lay Area",                 "{nickname} would cover **{layarea:,.3mu}** of area laying down.",                  "{layarea:,.3mu}",                                      is_shown=False,                                 requires=["height", "width"],           power=2,    type=AV,                                default_from=lambda s: s["height"] * s["width"]),
    Stat("footarea",                "Foot Area",                "{nickname}'s foot would cover **{footarea:,.3mu}** of area.",                      "{footarea:,.3mu}",                                     is_shown=False,                                 requires=["footlength", "footwidth"],   power=2,    type=AV,                                default_from=(lambda s: s["footlength"] * s["footwidth"]), tags = ["foot"]),
    Stat("fingertiparea",           "Fingertip Area",           "{nickname}'s fingertip would cover **{fingertiparea:,.3mu}** of area.",            "{fingertiparea:,.3mu}",                                is_shown=False,                                 requires=["fingertiplength"],           power=2,    type=AV,                                default_from=(lambda s: s["fingertiplength"] * s["fingertiplength"]), tags = ["hand"]),
    Stat("shoesize",                "Shoe Size",                "{nickname}'s shoe size is **{shoesize}**.",                                        "{shoesize}",                                                                                           requires=["footlength", "gender"],                  type=str,                               default_from=(lambda s: format_shoe_size(s["footlength"], s["gender"])), tags = ["foot"]),
    Stat("visibility",              "Visibility",               "You would need **{visibility}** to see {nickname}.",                               "*{nickname} would need {visibility} to be seen.*",     is_shown=lambda s: s["scale"] < 1,              requires=["height"],                                type=str,                               default_from=lambda s: calcVisibility(s["height"]))
]}


class ComplexEmbed:
    def __init__(self,
                 key: str,
                 format_title: Formatter,
                 format_embed: Formatter,
                 is_shown: Union[Callable[[dict[str, any]], bool], bool] = lambda s: True,
                 z: Optional[int] = None,
                 tags: list[str] = None,
                 inline: bool = True):
        self.key = key
        self.format_title = format_title
        self.format_embed = format_embed
        self.is_shown = (lambda s: is_shown) if isinstance(is_shown, bool) else is_shown
        self.z = z
        self.tags = tags or []
        self.inline = inline

    def to_embed_title(self, stats: StatBox):
        return run_statbox_formatter(self.format_title, stats)

    def to_embed_value(self, stats: StatBox):
        return run_statbox_formatter(self.format_embed, stats)

    def get_embed(self, stats: StatBox) -> dict:
        return {
            "name": self.to_embed_title(stats),
            "value": self.to_embed_value(stats),
            "inline": self.inline
        }


complex_embeds = {s.key: s for s in [
    ComplexEmbed(
        "height",
        lambda s: s.get_embed_title("height"),
        lambda s:
            f"{s.get_embed_value('height')}"
            f"\n*{s.get_embed_value('scale')} scale*"
            + (f"\n*{s.get_embed_value('visibility')}" if s.is_shown('visibility') else ""),
        z = 1, tags = ["height"]
    ),
    ComplexEmbed(
        "weight",
        lambda s: s.get_embed_title("weight"),
        lambda s:
            f"{s.get_embed_value('weight')}"
            f"\n*{s.get_embed_value('cubescale')} scale*",
        z = 2
    ),
    ComplexEmbed(
        "footlength",
        lambda s: "[FOOTNAME] length",
        lambda s:
            f"{s.get_embed_value('footlength')}"
            f"\n({s.get_embed_value('shoesize')})"
    ),
    ComplexEmbed(
        "simplespeeds",
        "Speeds",
        lambda s: "\n".join(s.get_embed_value(f) for f in ["walkperhour", "runperhour", "climbperhour", "swimperhour"])
    ),
    ComplexEmbed(
        "speeds",
        "Speeds",
        lambda s: "\n".join(s.get_embed_value(f) for f in ["walkperhour", "runperhour", "climbperhour", "crawlperhour", "swimperhour", "driveperhour", "spaceshipperhour"]),
        z = -2,
        inline=False
    ),
    ComplexEmbed(
        "bases",
        "Character Bases",
        lambda s: f"{s.get_embed_value('height')} | {s.get_embed_value('weight')}",
        z = -1
    )
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


T = TypeVar('T', Stat, StatValue)


class StatBox:
    def __init__(self, stats: dict[str, StatValue]):
        self.stats = stats
        self.values = {k: sv.value for k, sv in self.stats.items()}

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

    def sorted_keys(self) -> list[str]:
        li = []
        positives = {k: v for (k, v) in self.stats.items() if v.stat.z and v.stat.z >= 0}
        neutrals = {k: v for (k, v) in self.stats.items() if v.stat.z is None}
        negatives = {k: v for (k, v) in self.stats.items() if v.stat.z and v.stat.z < 0}
        for k, v in sorted(positives.items(), key = lambda item: item[1].stat.z):
            li.append(k)
        for k, v in neutrals.items():
            li.append(k)
        for k, v in sorted(negatives.items(), key = lambda item: item[1].stat.z):
            li.append(k)
        return li

    @classmethod
    def load(cls, playerStats: PlayerStats) -> StatBox:
        return cls.process(all_stats, lambda s, vals: s.set(playerStats, vals))

    def scale(self, scale_value: Decimal) -> StatBox:
        return self.process(self.stats, lambda s, vals: s.scale(scale_value, vals))

    def get_value(self, key: str) -> Any:
        return self.stats[key].value

    def get_string(self, key: str) -> str:
        return self.stats[key].to_string(self.values)

    def is_shown(self, key: str) -> bool:
        return self.stats[key].is_shown(self.values)

    def get_embed_title(self, key: str) -> str:
        return self.stats[key].to_embed_title(self.values)

    def get_embed_value(self, key: str) -> str:
        return self.stats[key].to_embed_value(self.values)

    def get_embed(self, key: str) -> dict:
        return {
            "name": self.get_embed_title(key),
            "value": self.get_embed_value(key),
            "inline": True
        }

    def __iter__(self):
        for k in self.stats.keys():
            yield k


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
        self.baseheight = self.basestats.values["height"]               # UNUSED
        self.baseweight = self.basestats.values["weight"]               # UNUSED
        self.pawtoggle = userdata.pawtoggle                             # UNUSED
        self.furtoggle = userdata.furtoggle                             # UNUSED

        # What do I do with these?
        self.incomprehensible = userdata.incomprehensible               # UNUSED
        self.macrovision_model = userdata.macrovision_model             # UNUSED
        self.macrovision_view = userdata.macrovision_view               # UNUSED

        # Other stats
        self.height = self.stats.values["height"]                       # USED
        self.weight = self.stats.values["weight"]                       # UNUSED
        self.width = self.stats.values["width"]                         # USED

        # These are like, the user settable ones?
        self.hairlength = self.stats.values["hairlength"]               # UNUSED
        self.taillength = self.stats.values["taillength"]               # UNUSED
        self.earheight = self.stats.values["earheight"]                 # UNUSED
        self.liftstrength = self.stats.values["liftstrength"]           # UNUSED
        self.footlength = self.stats.values["footlength"]               # USED

        # How does this one work??
        self.shoesize = self.stats.values["shoesize"]                   # UNUSED

        # TODO: Is this accounted for in the new implementation?:
        # if userdata.pawtoggle:
        #     base_footwidth = SV(base_footlength * Decimal("2/3"))   # TODO: Temp number?
        # else:
        #     base_footwidth = SV(base_footlength * Decimal("2/5"))
        # self.footwidth = SV(base_footwidth * self.scale)
        self.footwidth = self.stats.values["footwidth"]                        # USED

        # OK, here's the stuff StatBox was actually made for.
        self.toeheight = self.stats.values["toeheight"]                        # UNUSED
        self.shoeprintdepth = self.stats.values["shoeprintdepth"]              # UNUSED
        self.pointerlength = self.stats.values["pointerlength"]                # UNUSED
        self.thumbwidth = self.stats.values["thumbwidth"]                      # UNUSED
        self.fingertiplength = self.stats.values["fingertiplength"]            # USED
        self.fingerprintdepth = self.stats.values["fingerprintdepth"]          # UNUSED
        self.threadthickness = self.stats.values["threadthickness"]            # UNUSED
        self.hairwidth = self.stats.values["hairwidth"]                        # UNUSED
        self.nailthickness = self.stats.values["nailthickness"]                # UNUSED
        self.eyewidth = self.stats.values["eyewidth"]                          # UNUSED
        self.jumpheight = self.stats.values["jumpheight"]                      # UNUSED

        # Yeah, I don't think we recreated these.
        # =======================================
        self.avgheightcomp = SV(AVERAGE_HEIGHT * self.stats.values["viewscale"])        # USED
        self.avgweightcomp = WV(DEFAULT_WEIGHT * self.stats.values["viewscale"] ** 3)   # UNUSED

        viewangle = calcViewAngle(self.height, average_height)
        self.avglookangle = abs(viewangle)                              # UNUSED
        self.avglookdirection = "up" if viewangle >= 0 else "down"      # UNUSED

        # base_average_ratio = self.baseheight / average_height  # TODO: Make this a property on userdata?
        # 11/26/2023: Wait, don't, do something else
        # =======================================

        # Speeds
        self.walkperhour = self.stats.values["walkperhour"]                    # USED
        self.runperhour = self.stats.values["runperhour"]                      # USED
        self.swimperhour = self.stats.values["swimperhour"]                    # USED
        self.climbperhour = self.stats.values["climbperhour"]                  # USED
        self.crawlperhour = self.stats.values["crawlperhour"]                  # USED
        self.driveperhour = self.stats.values["driveperhour"]                  # UNUSED
        self.spaceshipperhour = self.stats.values["spaceshipperhour"]          # UNUSED

        # This got ignored in the port somehow.
        # self.spaceshipperhour = SV(average_spaceshipperhour * self.scale)

        # Step lengths
        self.walksteplength = self.stats.values["walksteplength"]              # USED
        self.runsteplength = self.stats.values["runsteplength"]                # UNUSED
        self.climbsteplength = self.stats.values["climbsteplength"]            # UNUSED
        self.crawlsteplength = self.stats.values["crawlsteplength"]            # UNUSED
        self.swimsteplength = self.stats.values["swimsteplength"]              # UNUSED

        # The rest of it, I guess.
        self.horizondistance = self.stats.values["horizondistance"]            # UNUSED
        self.terminalvelocity = self.stats.values["terminalvelocity"]          # UNUSED
        self.fallproof = self.stats.values["fallproof"]                        # UNUSED
        self.fallproofcheck = self.stats.values["fallprooficon"]               # UNUSED
        self.visibility = self.stats.values["visibility"]                      # UNUSED

        self.simplespeeds = complex_embeds["simplespeeds"].to_embed_value(self.stats)

    def getFormattedStat(self, stat: str):
        # "foot": f"'s {self.footname.lower()} is **{self.footlength:,.3mu}** long and **{self.footwidth:,.3mu}** wide. ({self.shoesize})",
        try:
            mapped_stat = statmap[stat]
        except KeyError:
            return None

        returndict = {k: self.stats.get_string(k) for k in self.stats}

        return_stat = returndict.get(mapped_stat)
        if self.incomprehensible:
            return_stat = glitch_string(return_stat)
        return return_stat

    def __str__(self):
        return (f"<PersonStats NICKNAME = {self.stats.values['nickname']!r}, TAG = {self.tag!r}, GENDER = {self.stats.values['gender']!r}, "
                f"HEIGHT = {self.stats.values['height']!r}, BASEHEIGHT = {self.stats.values['baseheight']!r}, VIEWSCALE = {self.stats.values['viewscale']!r}, "
                f"WEIGHT = {self.stats.values['weight']!r}, BASEWEIGHT = {self.stats.values['baseweight']!r}, FOOTNAME = {self.stats.values['footname']!r}, "
                f"HAIRNAME = {self.stats.values['hairname']!r}, PAWTOGGLE = {self.stats.values['pawtoggle']!r}, FURTOGGLE = {self.stats.values['furtoggle']!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}"
                f"HAIRLENGTH = {self.stats.values['hairlength']!r}, TAILLENGTH = {self.stats.values['taillength']!r}, EARHEIGHT = {self.stats.values['earheight']!r},"
                f"LIFTSTRENGTH = {self.stats.values['liftstrength']!r}, FOOTLENGTH = {self.stats.values['footlength']!r}, "
                f"WALKPERHOUR = {self.stats.values['walkperhour']!r}, RUNPERHOUR = {self.stats.values['runperhour']!r}, VISIBILITY = {self.stats.values['visibility']!r}>")

    def __repr__(self):
        return str(self)

    def toEmbed(self, requesterID = None):
        requestertag = f"<@!{requesterID}>"
        embed = Embed(title=f"Stats for {self.nickname}",
                      description=f"*Requested by {requestertag}*",
                      color=colors.cyan)
        embed.set_author(name=f"SizeBot {__version__}")
        embed.add_field(**complex_embeds["height"].get_embed(self.stats))
        embed.add_field(**complex_embeds["weight"].get_embed(self.stats))
        embed.add_field(**complex_embeds["footlength"].get_embed(self.stats))
        for stat_name in self.stats.sorted_keys():
            if self.stats.is_shown(stat_name):
                embed.add_field(**self.stats.get_embed(stat_name))
        embed.add_field(**complex_embeds["speeds"].get_embed(self.stats))
        embed.add_field(**complex_embeds["bases"].get_embed(self.basestats))

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
