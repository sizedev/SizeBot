from __future__ import annotations
# from collections.abc import Callable

from copy import copy
from typing import Any, Literal, Optional, TypeVar, Callable
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
from sizebot.lib.utils import minmax, pretty_time_delta, url_safe

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

ValueDict = dict[str, Any]


def wrap_str(f: str | Callable[[ValueDict], str]) -> Callable[[ValueDict], str]:
    if isinstance(f, str):
        def wrapped(values: ValueDict) -> str:
            return f.format(**values)
        return wrapped
    else:
        return f


def wrap_str_statbox(f: str | Callable[[StatBox], str]) -> Callable[[StatBox], str]:
    if isinstance(f, str):
        def wrapped(statbox: StatBox) -> str:
            return f
        return wrapped
    else:
        return f


def wrap_bool(f: bool | Callable[[ValueDict], bool]) -> Callable[[ValueDict], bool]:
    if isinstance(f, bool):
        def wrapped(values: ValueDict) -> bool:
            return bool
        return wrapped
    else:
        return f


def grouped_z(z: int) -> tuple[int, int]:
    if z is None:
        return (1, 0)
    elif z < 0:
        return (2, z)
    else:
        return (0, z)


class StatDef:
    def __init__(self,
                 key: str,
                 format_title: Callable[[ValueDict], str] | str,
                 format_string: Callable[[ValueDict], str] | str,
                 format_embed: Callable[[ValueDict], str] | str,
                 is_shown: Callable[[ValueDict], bool] | bool = True,
                 userkey: Optional[str] = None,
                 calc_from: Optional[Callable[[ValueDict], Any]] = None,
                 power: Optional[int] = None,
                 requires: list[str] = None,
                 type: Optional[Callable[[Any], Any]] = None,
                 z: Optional[int] = None,
                 tags: list[str] = None
                 ):
        self.key = key
        self.format_title = wrap_str(format_title)
        self.format_string = wrap_str(format_string)
        self.format_embed = wrap_str(format_embed)
        self.is_shown = wrap_bool(is_shown)
        self.requires = requires or []
        self.power = power
        self.userkey = userkey
        self.calc_from = calc_from
        self.type = type
        self.orderkey = grouped_z(z)
        self.tags = tags or []

    def calc(self,
             sb: StatBox,
             values: dict[str, Any],
             *,
             userstats: PlayerStats = None,
             scale: Decimal = 1,
             old_value: Any = None
             ) -> None | Stat:
        value = old_value
        if value is None:
            if any(r not in values for r in self.requires):
                return
            if self.userkey is not None:
                value = userstats[self.userkey]
            if value is None and self.calc_from is not None:
                value = self.calc_from(values)

        if value is not None and self.power:
            # existing values with power attribute can be scaled
            value = value * (scale ** self.power)
        if value is not None and self.type:
            value = self.type(value)
        return Stat(sb, self, value)


class Stat:
    def __init__(self, sb: StatBox, definition: StatDef, value: Any):
        self.sb = sb
        self.definition = definition
        self.value = value

    @property
    def key(self):
        return self.definition.key

    @property
    def orderkey(self):
        return self.definition.orderkey

    @property
    def tags(self):
        return self.definition.tags

    def scale(self, sb: StatBox, scale: Decimal, values: dict[str, Any]) -> None | Stat:
        if self.value is None:
            value = None
        elif self.definition.power is not None:
            T = type(self.value)
            value = T(self.value * (scale ** self.definition.power))
        elif self.definition.calc_from:
            if any(r not in values for r in self.definition.requires):
                return
            value = self.definition.calc_from(values)
        else:
            value = self.value
        if self.definition.type and value is not None:
            value = self.definition.type(value)
        return Stat(sb, self.definition, value)

    def to_string(self) -> str:
        if self.value is None:
            return f"The {self.definition.format_title(self.sb.values)} stat is unavailable for this user."
        return self.definition.format_string(self.sb.values)

    def is_shown(self) -> bool:
        return self.definition.is_shown(self.sb.values)

    def to_embed_title(self):
        return self.definition.format_title(self.sb.values)

    def get_embed_value(self):
        return self.definition.format_embed(self.sb.values)

    def get_embed(self) -> dict:
        return {
            "name": self.to_embed_title(),
            "value": self.get_embed_value(),
            "inline": True
        }

    def __str__(self):
        values = {}     # TODO: Fix this
        return f"{self.definition.format_title(values)}: {self.value}"


CHK_Y = "✅"
CHK_N = "❎"

all_stats = {s.key: s for s in [
    StatDef("nickname",                "Nickname",                 "{nickname}",                                                                       "{nickname}",                                                                                           is_shown=False,                                                                                     type=str,       userkey="nickname"),
    StatDef("scale",                   "Scale",                    lambda s: format_scale(s['scale']),                                                 lambda s: format_scale(s['scale']),                                                                                                                                                             power=1,    type=Decimal,   userkey="scale"),
    StatDef("viewscale",               "Viewscale",                lambda s: format_scale(s['viewscale']),                                             lambda s: format_scale(s['viewscale']),                                                                 is_shown=False,                                 requires=["scale"],                                 type=Decimal,                           calc_from=lambda s: 1 / s["scale"]),
    StatDef("squarescale",             "Square Scale",             lambda s: format_scale(s['squarescale']),                                           lambda s: format_scale(s['squarescale']),                                                               is_shown=False,                                 requires=["scale"],                     power=2,    type=Decimal,                           calc_from=lambda s: s["scale"] ** 2),
    StatDef("cubescale",               "Cube Scale",               lambda s: format_scale(s['cubescale']),                                             lambda s: format_scale(s['cubescale']),                                                                 is_shown=False,                                 requires=["scale"],                     power=3,    type=Decimal,                           calc_from=lambda s: s["scale"] ** 3),
    StatDef("height",                  "Height",                   "{nickname}'s current height is **{height:,.3mu}**, or {scale} scale.",             "{height:,.3mu}",                                                                                                                                                                               power=1,    type=SV,        userkey="height",                                                                                               tags = ["height"]),
    StatDef("weight",                  "Weight",                   "{nickname}'s current weight is **{weight:,.3mu}**.",                               "{weight:,.3mu}",                                                                                                                                                                               power=3,    type=WV,        userkey="weight"),
    StatDef("gender",                  "Gender",                   "{nickname}'s gender is {gender}.",                                                 "{gender}",                                                                                             is_shown=False,                                                                                     type=str,       userkey="gender"),  # TODO: Should this be autogender?
    StatDef("averagescale",            "Average Scale",            "{nickname} is {averagescale} times taller than an average person.",                "{averagescale}",                                                                                       is_shown=False,                                 requires=["height"],                    power=1,    type=Decimal,                           calc_from=lambda s: s["height"] / AVERAGE_HEIGHT),
    StatDef("hairlength",              "Hair Length",              "{nickname}'s hair is **{hairlength:,.3mu}** long.",                                "{hairlength:,.3mu}",                                                                                   is_shown=lambda s: s["hairlength"],                                                     power=1,    type=SV,        userkey="hairlength"),
    StatDef("taillength",              "Tail Length",              "{nickname}'s tail is **{taillength:,.3mu}** long.",                                "{taillength:,.3mu}",                                                                                   is_shown=lambda s: s["taillength"],                                                     power=1,    type=SV,        userkey="taillength",                                                                                           tags = ["furry"]),
    StatDef("earheight",               "Ear Height",               "{nickname}'s ear is **{earheight:,.3mu}** tall.",                                  "{earheight:,.3mu}",                                                                                    is_shown=lambda s: s["earheight"],                                                      power=1,    type=SV,        userkey="earheight",                                                                                            tags = ["furry"]),
    StatDef("footlength",              "Foot Length",              "{nickname}'s foot is **{footlength:,.3mu}** long.",                                "{footlength:,.3mu}",                                                                                   is_shown=False,                                 requires=["height"],                    power=1,    type=SV,        userkey="footlength",   calc_from=lambda s: s["height"] / 7,                                                 tags = ["foot"]),
    StatDef("liftstrength",            "Lift Strength",            "{nickname} can lift {liftstrength:,.3mu}.",                                        "{liftstrength:,.3mu}",                                                                                                                                 requires=["height"],                    power=3,    type=WV,        userkey="liftstrength", calc_from=lambda s: DEFAULT_LIFT_STRENGTH),
    StatDef("footwidth",               "Foot Width",               "{nickname}'s foot is **{footwidth:,.3mu}** wide.",                                 "{footwidth:,.3mu}",                                                                                                                                    requires=["footlength"],                power=1,    type=SV,                                calc_from=(lambda s: s["footlength"] * Decimal(2 / 3)),                              tags = ["foot"]),
    StatDef("toeheight",               "Toe Height",               "{nickname}'s toe is **{toeheight:,.3mu}** thick.",                                 "{toeheight:,.3mu}",                                                                                    is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / 65),                                              tags = ["height"]),
    StatDef("shoeprintdepth",          "Shoeprint Depth",          "{nickname}'s shoeprint is **{shoeprintdepth:,.3mu}** deep.",                       "{shoeprintdepth:,.3mu}",                                                                               is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                calc_from=lambda s: s["height"] / 135),
    StatDef("pointerlength",           "Pointer Finger Length",    "{nickname}'s pointer finger is **{pointerlength:,.3mu}** long.",                   "{pointerlength:,.3mu}",                                                                                                                                requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / Decimal(17.26)),                                  tags = ["hand"]),
    StatDef("thumbwidth",              "Thumb Width",              "{nickname}'s thumb is **{thumbwidth:,.3mu}** wide.",                               "{thumbwidth:,.3mu}",                                                                                   is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / Decimal(69.06)),                                  tags = ["hand"]),
    StatDef("fingertiplength",         "Fingertip Length",         "{nickname}'s fingertip is **{fingertiplength:,.3mu}** long.",                      "{fingertiplength:,.3mu}",                                                                              is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / Decimal(95.95)),                                  tags = ["hand"]),
    StatDef("fingerprintdepth",        "Fingerprint Depth",        "{nickname}'s fingerprint is **{fingerprintdepth:,.3mu}** deep.",                   "{fingerprintdepth:,.3mu}",                                                                             is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / 35080),                                           tags = ["hand"]),
    StatDef("threadthickness",         "Thread Thickness",         "{nickname}'s clothing threads are **{threadthickness:,.3mu}** thick.",             "{threadthickness:,.3mu}",                                                                              is_shown=lambda s: s["scale"] > IS_LARGE,                                               power=1,    type=SV,                                calc_from=lambda s: DEFAULT_THREAD_THICKNESS),
    StatDef("hairwidth",               "Hair Width",               "{nickname}'s hair is **{hairwidth:,.3mu}** wide.",                                 "{hairwidth:,.3mu}",                                                                                    is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                calc_from=lambda s: s["height"] / 23387),
    StatDef("nailthickness",           "Nail Thickness",           "{nickname}'s nails are **{nailthickness:,.3mu}** thick.",                          "{nailthickness:,.3mu}",                                                                                is_shown=lambda s: s["scale"] > IS_VERY_LARGE,  requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] / 2920),                                            tags = ["hand"]),
    StatDef("eyewidth",                "Eye Width",                "{nickname}'s eyes are **{eyewidth:,.3mu}** wide.",                                 "{eyewidth:,.3mu}",                                                                                     is_shown=lambda s: s["scale"] > IS_LARGE,       requires=["height"],                    power=1,    type=SV,                                calc_from=lambda s: s["height"] / Decimal(73.083)),
    StatDef("jumpheight",              "Jump Height",              "{nickname} can jump **{jumpheight:,.3mu}** high.",                                 "{jumpheight:,.3mu}",                                                                                                                                   requires=["height"],                    power=1,    type=SV,                                calc_from=lambda s: s["height"] / Decimal(3.908)),
    StatDef("averagelookangle",        "Average Look Angle",       "{nickname} would have to look {averagelookangle} to see the average person.",      "{averagelookangle}",                                                                                   is_shown=False,                                 requires=["height"],                                type=Decimal,                           calc_from=lambda s: abs(calcViewAngle(s["height"], AVERAGE_HEIGHT))),
    StatDef("averagelookdirection",    "Average Look Direction",   "...",                                                                              "{averagelookdirection}",                                                                               is_shown=False,                                 requires=["height"],                                type=str,                               calc_from=lambda s: "up" if calcViewAngle(s["height"], AVERAGE_HEIGHT) >= 0 else "down"),
    StatDef("walkperhour",             "Walk Per Hour",            "{nickname} walks **{walkperhour:,.3mu} per hour**.",                               emojis.walk + "{walkperhour:,.1M} per hour / {walkperhour:,.1U} per hour",                              is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_WALKPERHOUR * s["averagescale"]),                       tags = ["movement"]),
    StatDef("runperhour",              "Run Per Hour",             "{nickname} runs **{runperhour:,.3mu} per hour**.",                                 emojis.run + " {runperhour:,.1M} per hour / {runperhour:,.1U} per hour",                                is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_RUNPERHOUR * s["averagescale"]),                        tags = ["movement"]),
    StatDef("swimperhour",             "Swim Per Hour",            "{nickname} swims **{swimperhour:,.3mu} per hour**.",                               emojis.climb + " {swimperhour:,.1M} per hour / {swimperhour:,.1U} per hour",                            is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_SWIMPERHOUR * s["averagescale"]),                       tags = ["movement"]),
    StatDef("climbperhour",            "Climb Per Hour",           "{nickname} climbs **{climbperhour:,.3mu} per hour**.",                             emojis.crawl + " {climbperhour:,.1M} per hour / {climbperhour:,.1U} per hour",                          is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_CLIMBPERHOUR * s["averagescale"]),                      tags = ["movement"]),
    StatDef("crawlperhour",            "Crawl Per Hour",           "{nickname} crawls **{crawlperhour:,.3mu} per hour**.",                             emojis.swim + " {crawlperhour:,.1M} per hour / {crawlperhour:,.1U} per hour",                           is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_CRAWLPERHOUR * s["averagescale"]),                      tags = ["movement"]),
    StatDef("driveperhour",            "Drive Per Hour",           "{nickname} drives **{driveperhour:,.3mu} per hour**.",                             emojis.drive + " {driveperhour:,.1M} per hour / {driveperhour:,.1U} per hour",                          is_shown=False,                                                                         power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_DRIVEPERHOUR),                                          tags = ["movement"]),
    StatDef("spaceshipperhour",        "Spaceship Per Hour",       "{nickname} flys at spaceship at **{spaceshipperhour:,.3mu} per hour**.",           emojis.spaceship + " {spaceshipperhour:,.1M} per hour / {spaceshipperhour:,.1U} per hour",              is_shown=False,                                                                         power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_SPACESHIPPERHOUR),                                      tags = ["movement"]),
    StatDef("walksteplength",          "Walk Step Length",         "{nickname} takes **{walksteplength:,.3mu}** strides while walking.",               "{walksteplength:,.3mu}",                                                                               is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_WALKPERHOUR * s["averagescale"] / WALKSTEPSPERHOUR),    tags = ["movement"]),
    StatDef("runsteplength",           "Run Step Length",          "{nickname} takes **{runsteplength:,.3mu}** strides while runing.",                 "{runsteplength:,.3mu}",                                                                                is_shown=False,                                 requires=["averagescale"],              power=1,    type=SV,                                calc_from=(lambda s: AVERAGE_RUNPERHOUR * s["averagescale"] / RUNSTEPSPERHOUR),      tags = ["movement"]),
    StatDef("climbsteplength",         "Climb Step Length",        "{nickname} takes **{climbsteplength:,.3mu}** strides while climbing.",             "{climbsteplength:,.3mu}",                                                                              is_shown=False,                                 requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] * Decimal(1 / 2.5)),                                tags = ["movement"]),
    StatDef("crawlsteplength",         "Crawl Step Length",        "{nickname} takes **{crawlsteplength:,.3mu}** strides while crawling.",             "{crawlsteplength:,.3mu}",                                                                              is_shown=False,                                 requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] * Decimal(1 / 2.577)),                              tags = ["movement"]),
    StatDef("swimsteplength",          "Swim Step Length",         "{nickname} takes **{swimsteplength:,.3mu}** strides while swiming.",               "{swimsteplength:,.3mu}",                                                                               is_shown=False,                                 requires=["height"],                    power=1,    type=SV,                                calc_from=(lambda s: s["height"] * Decimal(6 / 7)),                                  tags = ["movement"]),
    StatDef("horizondistance",         "View Distance to Horizon", "{nickname} can see **{horizondistance:,.3mu}** to the horizon.",                   "{horizondistance:,.3mu}",                                                                              is_shown=False,                                 requires=["height"],                                type=SV,                                calc_from=lambda s: calcHorizon(s["height"])),
    StatDef("terminalvelocity",        "Terminal Velocity",        "{nickname}'s terminal velocity is **{terminalvelocity:,.3mu} per hour.**",         lambda s: f"{s['terminalvelocity']:,.1M} per second\n({s['terminalvelocity']:,.1U} per second)" + ("\n*This user can safely fall from any height.*" if s["fallproof"] else ""),     requires=["weight", "averagescale"],    type=SV,                calc_from=lambda s: terminal_velocity(s["weight"], AVERAGE_HUMAN_DRAG_COEFFICIENT * s["averagescale"] ** Decimal(2))),
    StatDef("fallproof",               "Fallproof",                lambda s: f"""{s['nickname']} {'is' if s['fallproof'] else "isn't"} fallproof.""",  lambda s: CHK_Y if s['fallproof'] else CHK_N,                                                           is_shown=False,                                 requires=["terminalvelocity"],                      type=bool,                              calc_from=lambda s: s["terminalvelocity"] < FALL_LIMIT),
    StatDef("fallprooficon",           "Fallproof Icon",           lambda s: CHK_Y if s['fallproof'] else CHK_N,                                       lambda s: CHK_Y if s['fallproof'] else CHK_N,                                                           is_shown=False,                                 requires=["fallproof"],                             type=str,                               calc_from=lambda s: emojis.voteyes if s["fallproof"] else emojis.voteno),
    StatDef("width",                   "Width",                    "{nickname} is **{width:,.3mu}** wide.",                                            "{width:,.3mu}",                                                                                        is_shown=False,                                 requires=["height"],                    power=1,    type=SV,                                calc_from=lambda s: s["height"] * Decimal(4 / 17)),
    StatDef("soundtraveltime",         "Sound Travel Time",        "It would take sound **{soundtraveltime:,.3}** to travel {nickname}'s height.",     "{soundtraveltime:,.3mu}",                                                                              is_shown=False,                                 requires=["height"],                    power=1,    type=TV,                                calc_from=lambda s: s["height"] * ONE_SOUNDSECOND),
    StatDef("lighttraveltime",         "Light Travel Time",        "It would take light **{lighttraveltime:,.3}** to travel {nickname}'s height.",     "{lighttraveltime:,.3mu}",                                                                              is_shown=False,                                 requires=["height"],                    power=1,    type=TV,                                calc_from=lambda s: s["height"] * ONE_LIGHTSECOND),
    StatDef("caloriesneeded",          "Calories Needed",          "{nickname} needs **{caloriesneeded:,.0d}** calories per day.",                     "{caloriesneeded:,.0d}",                                                                                is_shown=False,                                                                         power=3,    type=Decimal,                           calc_from=lambda s: AVERAGE_CAL_PER_DAY),
    StatDef("waterneeded",             "Water Needed",             "{nickname} needs **{waterneeded:,.3mu}** of water per day.",                       "{waterneeded:,.3mu}",                                                                                  is_shown=False,                                                                         power=3,    type=WV,                                calc_from=lambda s: AVERAGE_WATER_PER_DAY),
    StatDef("layarea",                 "Lay Area",                 "{nickname} would cover **{layarea:,.3mu}** of area laying down.",                  "{layarea:,.3mu}",                                                                                      is_shown=False,                                 requires=["height", "width"],           power=2,    type=AV,                                calc_from=lambda s: s["height"] * s["width"]),
    StatDef("footarea",                "Foot Area",                "{nickname}'s foot would cover **{footarea:,.3mu}** of area.",                      "{footarea:,.3mu}",                                                                                     is_shown=False,                                 requires=["footlength", "footwidth"],   power=2,    type=AV,                                calc_from=(lambda s: s["footlength"] * s["footwidth"]),                              tags = ["foot"]),
    StatDef("fingertiparea",           "Fingertip Area",           "{nickname}'s fingertip would cover **{fingertiparea:,.3mu}** of area.",            "{fingertiparea:,.3mu}",                                                                                is_shown=False,                                 requires=["fingertiplength"],           power=2,    type=AV,                                calc_from=(lambda s: s["fingertiplength"] * s["fingertiplength"]),                   tags = ["hand"]),
    StatDef("shoesize",                "Shoe Size",                "{nickname}'s shoe size is **{shoesize}**.",                                        "{shoesize}",                                                                                                                                           requires=["footlength", "gender"],                  type=str,                               calc_from=(lambda s: format_shoe_size(s["footlength"], s["gender"])),                tags = ["foot"]),
    StatDef("visibility",              "Visibility",               "You would need **{visibility}** to see {nickname}.",                               "*{nickname} would need {visibility} to be seen.*",                                                     is_shown=lambda s: s["scale"] < 1,              requires=["height"],                                type=str,                               calc_from=lambda s: calcVisibility(s["height"]))
]}


class ComplexEmbed:
    def __init__(self,
                 key: str,
                 format_title: Callable[[StatBox], str] | str,
                 format_embed: Callable[[StatBox], str] | str,
                 is_shown: Callable[[ValueDict], bool] | bool = True,
                 z: Optional[int] = None,
                 tags: list[str] = None,
                 inline: bool = True):
        self.key = key
        self.format_title = wrap_str_statbox(format_title)
        self.format_embed = wrap_str_statbox(format_embed)
        self.is_shown = wrap_bool(is_shown)
        self.orderkey = grouped_z(z)
        self.tags = tags or []
        self.inline = inline

    def to_embed_title(self, stats: StatBox):
        return self.format_title(stats)

    def to_embed_value(self, stats: StatBox):
        return self.format_embed(stats)

    def get_embed(self, stats: StatBox) -> dict:
        return {
            "name": self.to_embed_title(stats),
            "value": self.to_embed_value(stats),
            "inline": self.inline
        }


complex_embeds = {s.key: s for s in [
    ComplexEmbed(
        "height",
        lambda s: s['height'].get_embed_title(),
        lambda s:
            f"{s['height'].get_embed_value()}"
            f"\n*{s['scale'].get_embed_value()} scale*"
            + (f"\n*{s['visibility'].get_embed_value()}" if s['visibility'].is_shown() else ""),
        z = 1,
        tags = ["height"]
    ),
    ComplexEmbed(
        "weight",
        lambda s: s['weight'].get_embed_title(),
        lambda s:
            f"{s['weight'].get_embed_value()}"
            f"\n*{s['cubescale'].get_embed_value()} scale*",
        z = 2
    ),
    ComplexEmbed(
        "footlength",
        lambda s: "[FOOTNAME] length",
        lambda s:
            f"{s['footlength'].get_embed_value()}"
            f"\n({s['shoesize'].get_embed_value()})"
    ),
    ComplexEmbed(
        "simplespeeds",
        "Speeds",
        lambda s: "\n".join(s[f].get_embed_value() for f in ["walkperhour", "runperhour", "climbperhour", "swimperhour"])
    ),
    ComplexEmbed(
        "speeds",
        "Speeds",
        lambda s: "\n".join(s[f].get_embed_value() for f in ["walkperhour", "runperhour", "climbperhour", "crawlperhour", "swimperhour", "driveperhour", "spaceshipperhour"]),
        z = -2,
        inline=False
    ),
    ComplexEmbed(
        "bases",
        "Character Bases",
        lambda s: f"{s['height'].get_embed_value()} | {s['weight'].get_embed_value()}",
        z = -1
    )
]}


def generate_statmap() -> dict[str, str]:
    statmap = {}
    for stat, aliases in stataliases.items():
        if stat not in all_stats:
            raise Exception(f"WTF MATE {stat}")
        for alias in aliases:
            statmap[alias] = stat
    for stat in all_stats.keys():
        statmap[stat] = stat
    return statmap


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
statmap = generate_statmap()


IN = TypeVar('IN')
OUT = TypeVar('OUT')


def process_queue(source: list[IN], _process: Callable[[IN], None | OUT]) -> list[OUT]:
    queued: list[Any] = source.copy()
    processing: list[Any] = []
    processed: list[Any] = []

    while queued:
        processing = queued
        queued = []
        for s in processing:
            result = _process(s)
            if result is None:
                # If we can't set/scale it, queue it for later
                queued.append(s)
            else:
                # If it's set/scaled, just append to the processed stats
                processed.append(result)
        # If no progress
        if len(queued) == len(processing):
            raise errors.UnfoundStatException(queued)

    return processed


class StatBox:
    def __init__(self):
        self.stats: dict[str, Stat] = {}
        self.values: dict[str, Any] = {}
        self.sorted_stats: list[Stat] = []

    def set_stats(self, stats: list[Stat]):
        self.stats = {sv.key: sv for sv in stats}
        self.values = {sv.key: sv.value for sv in stats}
        self.sorted_stats = sorted(stats, key = lambda s: s.orderkey)

    @classmethod
    def load(cls, userstats: PlayerStats) -> StatBox:
        values: dict[str, Any] = {}
        sb = StatBox()

        def _process(sdef: StatDef):
            result = sdef.calc(sb, values, userstats=userstats)
            if result is not None:
                values[result.key] = result.value
            return result
        stats = process_queue(all_stats, _process)
        sb.set_stats(stats)
        return sb

    def scale(self, scale_value: Decimal) -> StatBox:
        values: dict[str, Any] = {}
        sb = StatBox()

        def _process(s: Stat):
            result = s.definition.calc(sb, values, scale=scale_value, old_value=s.value)
            if result is not None:
                values[result.key] = result.value
            return result
        stats = process_queue(self.stats, _process)
        sb.set_stats(stats)
        return sb

    def __iter__(self):
        for k in self.sorted_stats:
            yield k

    def __getitem__(self, k: str):
        return self.stats[k]


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

        if descmap[mapped_key] is None:
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
        self.footwidth = self.stats["footwidth"].values                        # USED

        # OK, here's the stuff StatBox was actually made for.
        self.toeheight = self.stats["toeheight"].values                        # UNUSED
        self.shoeprintdepth = self.stats["shoeprintdepth"].values              # UNUSED
        self.pointerlength = self.stats["pointerlength"].values                # UNUSED
        self.thumbwidth = self.stats["thumbwidth"].values                      # UNUSED
        self.fingertiplength = self.stats["fingertiplength"].values            # USED
        self.fingerprintdepth = self.stats["fingerprintdepth"].values          # UNUSED
        self.threadthickness = self.stats["threadthickness"].values            # UNUSED
        self.hairwidth = self.stats["hairwidth"].values                        # UNUSED
        self.nailthickness = self.stats["nailthickness"].values                # UNUSED
        self.eyewidth = self.stats["eyewidth"].values                          # UNUSED
        self.jumpheight = self.stats["jumpheight"].values                      # UNUSED

        # Yeah, I don't think we recreated these.
        # =======================================
        self.avgheightcomp = SV(AVERAGE_HEIGHT * self.stats["viewscale"].values)        # USED
        self.avgweightcomp = WV(DEFAULT_WEIGHT * self.stats["viewscale"].values ** 3)   # UNUSED

        viewangle = calcViewAngle(self.height, average_height)
        self.avglookangle = abs(viewangle)                              # UNUSED
        self.avglookdirection = "up" if viewangle >= 0 else "down"      # UNUSED

        # base_average_ratio = self.baseheight / average_height  # TODO: Make this a property on userdata?
        # 11/26/2023: Wait, don't, do something else
        # =======================================

        # Speeds
        self.walkperhour = self.stats["walkperhour"].values                    # USED
        self.runperhour = self.stats["runperhour"].values                      # USED
        self.swimperhour = self.stats["swimperhour"].values                    # USED
        self.climbperhour = self.stats["climbperhour"].values                  # USED
        self.crawlperhour = self.stats["crawlperhour"].values                  # USED
        self.driveperhour = self.stats["driveperhour"].values                  # UNUSED
        self.spaceshipperhour = self.stats["spaceshipperhour"].values          # UNUSED

        # This got ignored in the port somehow.
        # self.spaceshipperhour = SV(average_spaceshipperhour * self.scale)

        # Step lengths
        self.walksteplength = self.stats["walksteplength"].values              # USED
        self.runsteplength = self.stats["runsteplength"].values                # UNUSED
        self.climbsteplength = self.stats["climbsteplength"].values            # UNUSED
        self.crawlsteplength = self.stats["crawlsteplength"].values            # UNUSED
        self.swimsteplength = self.stats["swimsteplength"].values              # UNUSED

        # The rest of it, I guess.
        self.horizondistance = self.stats["horizondistance"].values            # UNUSED
        self.terminalvelocity = self.stats["terminalvelocity"].values          # UNUSED
        self.fallproof = self.stats["fallproof"].values                        # UNUSED
        self.fallproofcheck = self.stats["fallprooficon"].values               # UNUSED
        self.visibility = self.stats["visibility"].values                      # UNUSED

        self.simplespeeds = complex_embeds["simplespeeds"].to_embed_value(self.stats)

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
        embed.add_field(**complex_embeds["height"].get_embed(self.stats))
        embed.add_field(**complex_embeds["weight"].get_embed(self.stats))
        embed.add_field(**complex_embeds["footlength"].get_embed(self.stats))

        for stat in self.stats:
            if stat.is_shown():
                embed.add_field(**stat.get_embed())
        embed.add_field(**complex_embeds["speeds"].get_embed(self.stats))
        embed.add_field(**complex_embeds["bases"].get_embed(self.basestats))

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
                embed.add_field(**stat.get_embed())

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
