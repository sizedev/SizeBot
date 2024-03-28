from __future__ import annotations

from functools import cached_property
from typing import Any, Literal, Optional, TypeVar, Callable
import math
import re

from sizebot.lib import errors
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.freefall import terminal_velocity, AVERAGE_HUMAN_DRAG_COEFFICIENT
from sizebot.lib.units import SV, TV, WV, AV
from sizebot.lib.userdb import PlayerStats, DEFAULT_HEIGHT as average_height, DEFAULT_LIFT_STRENGTH, FALL_LIMIT


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


ValueDict = dict[str, Any]


def wrap_str(f: str | Callable[[StatBox], str]) -> Callable[[StatBox], str]:
    if isinstance(f, str):
        def wrapped(sb: StatBox) -> str:
            return f.format(**sb.values)
        return wrapped
    else:
        return f


def wrap_bool(f: bool | Callable[[ValueDict], bool]) -> Callable[[ValueDict], bool]:
    if isinstance(f, bool):
        def wrapped(values: ValueDict) -> bool:
            return f
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
                 title: Callable[[StatBox], str] | str,
                 string: Callable[[StatBox], str] | str,
                 body: Callable[[StatBox], str] | str,
                 is_shown: Callable[[StatBox], bool] | bool = True,
                 userkey: Optional[str] = None,
                 value: Optional[Callable[[ValueDict], Any]] = None,
                 power: Optional[int] = None,
                 requires: list[str] = None,
                 type: Optional[Callable[[Any], Any]] = None,
                 z: Optional[int] = None,
                 tags: list[str] = None,
                 inline: bool = True
                 ):
        self.key = key
        self.get_title = wrap_str(title)
        self.get_body = wrap_str(body)
        self.get_string = wrap_str(string)
        self.get_is_shown = wrap_bool(is_shown)
        self.userkey = userkey
        self.get_value = value
        self.requires = requires or []
        self.power = power
        self.type = type
        self.orderkey = grouped_z(z)
        self.tags = tags or []
        self.inline = inline

    def get_stat(self,
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
            if self.userkey is not None and userstats is not None:
                value = userstats[self.userkey]
            if value is None and self.get_value is not None:
                value = self.get_value(values)

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

    @cached_property
    def is_shown(self) -> bool:
        return self.definition.get_is_shown(self.sb)

    @cached_property
    def title(self):
        return self.definition.get_title(self.sb)

    @cached_property
    def body(self):
        return self.definition.get_body(self.sb)

    @cached_property
    def string(self) -> str:
        if self.value is None:
            return f"The {self.title} stat is unavailable for this user."
        return self.definition.get_string(self.sb)

    @cached_property
    def embed(self) -> dict:
        return {
            "name": self.title,
            "value": self.body,
            "inline": self.definition.inline
        }

    def __str__(self):
        return f"{self.title}: {self.value}"


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
        self.stats: list[Stat] = []
        self.stats_by_key: dict[str, Stat] = {}
        self.values: dict[str, Any] = {}

    def set_stats(self, stats: list[Stat]):
        self.stats = sorted(stats, key = lambda s: s.orderkey)
        self.stats_by_key = {sv.key: sv for sv in stats}
        self.values = {sv.key: sv.value for sv in stats}

    @classmethod
    def load(cls, userstats: PlayerStats) -> StatBox:
        values: dict[str, Any] = {}
        sb = StatBox()

        def _process(sdef: StatDef):
            result = sdef.get_stat(sb, values, userstats=userstats)
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
            result = s.definition.get_stat(sb, values, scale=scale_value, old_value=s.value)
            if result is not None:
                values[result.key] = result.value
            return result
        stats = process_queue(self.stats, _process)
        sb.set_stats(stats)
        return sb

    def __iter__(self):
        for k in self.stats:
            yield k

    def __getitem__(self, k: str):
        return self.stats_by_key[k]


CHK_Y = "✅"
CHK_N = "❎"

all_stats = [
    StatDef("nickname",                "Nickname",                      "{nickname}",                                                                       "{nickname}",                                                                                           is_shown=False,                                                                                              type=str,       userkey="nickname"),
    StatDef("scale",                   "Scale",                         lambda s: format_scale(s['scale'].value),                                           lambda s: format_scale(s['scale'].value),                                                                                                                                                                power=0,    type=Decimal,   userkey="scale"),
    StatDef("viewscale",               "Viewscale",                     lambda s: format_scale(s['viewscale'].value),                                       lambda s: format_scale(s['viewscale'].value),                                                           is_shown=False,                                          requires=["scale"],                     power=0,    type=Decimal,                           value=lambda v: 1 / v["scale"]),
    StatDef("squarescale",             "Square Scale",                  lambda s: format_scale(s['squarescale'].value),                                     lambda s: format_scale(s['squarescale'].value),                                                         is_shown=False,                                          requires=["scale"],                     power=2,    type=Decimal,                           value=lambda v: v["scale"] ** 2),
    StatDef("cubescale",               "Cube Scale",                    lambda s: format_scale(s['cubescale'].value),                                       lambda s: format_scale(s['cubescale'].value),                                                           is_shown=False,                                          requires=["scale"],                     power=3,    type=Decimal,                           value=lambda v: v["scale"] ** 3),
    StatDef("height",                  "Height",                        "{nickname}'s current height is **{height:,.3mu}**, or {scale} scale.",             "{height:,.3mu}",                                                                                       is_shown=False,                                                                                  power=1,    type=SV,        userkey="height",                                                                                            tags=["height"]),
    StatDef("weight",                  "Weight",                        "{nickname}'s current weight is **{weight:,.3mu}**.",                               "{weight:,.3mu}",                                                                                       is_shown=False,                                                                                  power=3,    type=WV,        userkey="weight"),
    StatDef("gender",                  "Gender",                        "{nickname}'s gender is {gender}.",                                                 "{gender}",                                                                                             is_shown=False,                                                                                              type=str,       userkey="gender"),  # TODO: Should this be autogender?
    StatDef("averagescale",            "Average Scale",                 "{nickname} is {averagescale} times taller than an average person.",                "{averagescale}",                                                                                       is_shown=False,                                          requires=["height"],                    power=1,    type=Decimal,                           value=lambda v: v["height"] / AVERAGE_HEIGHT),
    StatDef("hairlength",              "Hair Length",                   "{nickname}'s hair is **{hairlength:,.3mu}** long.",                                "{hairlength:,.3mu}",                                                                                   is_shown=lambda s: s["hairlength"].value,                                                        power=1,    type=SV,        userkey="hairlength"),
    StatDef("taillength",              "Tail Length",                   "{nickname}'s tail is **{taillength:,.3mu}** long.",                                "{taillength:,.3mu}",                                                                                   is_shown=lambda s: s["taillength"].value,                                                        power=1,    type=SV,        userkey="taillength",                                                                                        tags=["furry"]),
    StatDef("earheight",               "Ear Height",                    "{nickname}'s ear is **{earheight:,.3mu}** tall.",                                  "{earheight:,.3mu}",                                                                                    is_shown=lambda s: s["earheight"].value,                                                         power=1,    type=SV,        userkey="earheight",                                                                                         tags=["furry"]),
    StatDef("footlength",              "Foot Length",                   "{nickname}'s foot is **{footlength:,.3mu}** long.",                                "{footlength:,.3mu}",                                                                                   is_shown=False,                                          requires=["height"],                    power=1,    type=SV,        userkey="footlength",   value=lambda v: v["height"] / 7,                                                 tags=["foot"]),
    StatDef("liftstrength",            "Lift Strength",                 "{nickname} can lift {liftstrength:,.3mu}.",                                        "{liftstrength:,.3mu}",                                                                                                                                          requires=["height"],                    power=3,    type=WV,        userkey="liftstrength", value=lambda v: DEFAULT_LIFT_STRENGTH),
    StatDef("footwidth",               "Foot Width",                    "{nickname}'s foot is **{footwidth:,.3mu}** wide.",                                 "{footwidth:,.3mu}",                                                                                                                                             requires=["footlength"],                power=1,    type=SV,                                value=(lambda v: v["footlength"] * Decimal(2 / 3)),                              tags=["foot"]),
    StatDef("toeheight",               "Toe Height",                    "{nickname}'s toe is **{toeheight:,.3mu}** thick.",                                 "{toeheight:,.3mu}",                                                                                    is_shown=lambda s: s["scale"].value > IS_LARGE,          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / 65),                                              tags=["height"]),
    StatDef("shoeprintdepth",          "Shoeprint Depth",               "{nickname}'s shoeprint is **{shoeprintdepth:,.3mu}** deep.",                       "{shoeprintdepth:,.3mu}",                                                                               is_shown=lambda s: s["scale"].value > IS_LARGE,          requires=["height"],                    power=1,    type=SV,                                value=lambda v: v["height"] / 135),
    StatDef("pointerlength",           "Pointer Finger Length",         "{nickname}'s pointer finger is **{pointerlength:,.3mu}** long.",                   "{pointerlength:,.3mu}",                                                                                                                                         requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / Decimal(17.26)),                                  tags=["hand"]),
    StatDef("thumbwidth",              "Thumb Width",                   "{nickname}'s thumb is **{thumbwidth:,.3mu}** wide.",                               "{thumbwidth:,.3mu}",                                                                                   is_shown=lambda s: s["scale"].value > IS_LARGE,          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / Decimal(69.06)),                                  tags=["hand"]),
    StatDef("fingertiplength",         "Fingertip Length",              "{nickname}'s fingertip is **{fingertiplength:,.3mu}** long.",                      "{fingertiplength:,.3mu}",                                                                              is_shown=lambda s: s["scale"].value > IS_LARGE,          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / Decimal(95.95)),                                  tags=["hand"]),
    StatDef("fingerprintdepth",        "Fingerprint Depth",             "{nickname}'s fingerprint is **{fingerprintdepth:,.3mu}** deep.",                   "{fingerprintdepth:,.3mu}",                                                                             is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,     requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / 35080),                                           tags=["hand"]),
    StatDef("threadthickness",         "Thread Thickness",              "{nickname}'s clothing threads are **{threadthickness:,.3mu}** thick.",             "{threadthickness:,.3mu}",                                                                              is_shown=lambda s: s["scale"].value > IS_LARGE,                                                  power=1,    type=SV,                                value=lambda v: DEFAULT_THREAD_THICKNESS),
    StatDef("hairwidth",               "Hair Width",                    "{nickname}'s hair is **{hairwidth:,.3mu}** wide.",                                 "{hairwidth:,.3mu}",                                                                                    is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,     requires=["height"],                    power=1,    type=SV,                                value=lambda v: v["height"] / 23387),
    StatDef("nailthickness",           "Nail Thickness",                "{nickname}'s nails are **{nailthickness:,.3mu}** thick.",                          "{nailthickness:,.3mu}",                                                                                is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,     requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] / 2920),                                            tags=["hand"]),
    StatDef("eyewidth",                "Eye Width",                     "{nickname}'s eyes are **{eyewidth:,.3mu}** wide.",                                 "{eyewidth:,.3mu}",                                                                                     is_shown=lambda s: s["scale"].value > IS_LARGE,          requires=["height"],                    power=1,    type=SV,                                value=lambda v: v["height"] / Decimal(73.083)),
    StatDef("jumpheight",              "Jump Height",                   "{nickname} can jump **{jumpheight:,.3mu}** high.",                                 "{jumpheight:,.3mu}",                                                                                                                                            requires=["height"],                    power=1,    type=SV,                                value=lambda v: v["height"] / Decimal(3.908)),
    StatDef("averagelookangle",        "Average Look Angle",            "{nickname} would have to look {averagelookangle} to see the average person.",      "{averagelookangle}",                                                                                   is_shown=False,                                          requires=["height"],                                type=Decimal,                           value=lambda v: abs(calcViewAngle(v["height"], AVERAGE_HEIGHT))),
    StatDef("averagelookdirection",    "Average Look Direction",        "...",                                                                              "{averagelookdirection}",                                                                               is_shown=False,                                          requires=["height"],                                type=str,                               value=lambda v: "up" if calcViewAngle(v["height"], AVERAGE_HEIGHT) >= 0 else "down"),
    StatDef("walkperhour",             "Walk Per Hour",                 "{nickname} walks **{walkperhour:,.3mu} per hour**.",                               emojis.walk + "{walkperhour:,.1M} per hour / {walkperhour:,.1U} per hour",                              is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_WALKPERHOUR * v["averagescale"]),                       tags=["movement"]),
    StatDef("runperhour",              "Run Per Hour",                  "{nickname} runs **{runperhour:,.3mu} per hour**.",                                 emojis.run + " {runperhour:,.1M} per hour / {runperhour:,.1U} per hour",                                is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_RUNPERHOUR * v["averagescale"]),                        tags=["movement"]),
    StatDef("swimperhour",             "Swim Per Hour",                 "{nickname} swims **{swimperhour:,.3mu} per hour**.",                               emojis.climb + " {swimperhour:,.1M} per hour / {swimperhour:,.1U} per hour",                            is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_SWIMPERHOUR * v["averagescale"]),                       tags=["movement"]),
    StatDef("climbperhour",            "Climb Per Hour",                "{nickname} climbs **{climbperhour:,.3mu} per hour**.",                             emojis.crawl + " {climbperhour:,.1M} per hour / {climbperhour:,.1U} per hour",                          is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_CLIMBPERHOUR * v["averagescale"]),                      tags=["movement"]),
    StatDef("crawlperhour",            "Crawl Per Hour",                "{nickname} crawls **{crawlperhour:,.3mu} per hour**.",                             emojis.swim + " {crawlperhour:,.1M} per hour / {crawlperhour:,.1U} per hour",                           is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_CRAWLPERHOUR * v["averagescale"]),                      tags=["movement"]),
    StatDef("driveperhour",            "Drive Per Hour",                "{nickname} drives **{driveperhour:,.3mu} per hour**.",                             emojis.drive + " {driveperhour:,.1M} per hour / {driveperhour:,.1U} per hour",                          is_shown=False,                                                                                  power=1,    type=SV,                                value=(lambda v: AVERAGE_DRIVEPERHOUR),                                          tags=["movement"]),
    StatDef("spaceshipperhour",        "Spaceship Per Hour",            "{nickname} flys at spaceship at **{spaceshipperhour:,.3mu} per hour**.",           emojis.spaceship + " {spaceshipperhour:,.1M} per hour / {spaceshipperhour:,.1U} per hour",              is_shown=False,                                                                                  power=1,    type=SV,                                value=(lambda v: AVERAGE_SPACESHIPPERHOUR),                                      tags=["movement"]),
    StatDef("walksteplength",          "Walk Step Length",              "{nickname} takes **{walksteplength:,.3mu}** strides while walking.",               "{walksteplength:,.3mu}",                                                                               is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_WALKPERHOUR * v["averagescale"] / WALKSTEPSPERHOUR),    tags=["movement"]),
    StatDef("runsteplength",           "Run Step Length",               "{nickname} takes **{runsteplength:,.3mu}** strides while runing.",                 "{runsteplength:,.3mu}",                                                                                is_shown=False,                                          requires=["averagescale"],              power=1,    type=SV,                                value=(lambda v: AVERAGE_RUNPERHOUR * v["averagescale"] / RUNSTEPSPERHOUR),      tags=["movement"]),
    StatDef("climbsteplength",         "Climb Step Length",             "{nickname} takes **{climbsteplength:,.3mu}** strides while climbing.",             "{climbsteplength:,.3mu}",                                                                              is_shown=False,                                          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] * Decimal(1 / 2.5)),                                tags=["movement"]),
    StatDef("crawlsteplength",         "Crawl Step Length",             "{nickname} takes **{crawlsteplength:,.3mu}** strides while crawling.",             "{crawlsteplength:,.3mu}",                                                                              is_shown=False,                                          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] * Decimal(1 / 2.577)),                              tags=["movement"]),
    StatDef("swimsteplength",          "Swim Step Length",              "{nickname} takes **{swimsteplength:,.3mu}** strides while swiming.",               "{swimsteplength:,.3mu}",                                                                               is_shown=False,                                          requires=["height"],                    power=1,    type=SV,                                value=(lambda v: v["height"] * Decimal(6 / 7)),                                  tags=["movement"]),
    StatDef("horizondistance",         "View Distance to Horizon",      "{nickname} can see **{horizondistance:,.3mu}** to the horizon.",                   "{horizondistance:,.3mu}",                                                                              is_shown=False,                                          requires=["height"],                                type=SV,                                value=lambda v: calcHorizon(v["height"])),
    StatDef("terminalvelocity",        "Terminal Velocity",             "{nickname}'s terminal velocity is **{terminalvelocity:,.3mu} per hour.**",         lambda s: f"{s['terminalvelocity'].value:,.1M} per second\n({s['terminalvelocity'].value:,.1U} per second)" + ("\n*This user can safely fall from any height.*" if s["fallproof"].value else ""),     requires=["weight", "averagescale"],    type=SV,       value=lambda v: terminal_velocity(v["weight"], AVERAGE_HUMAN_DRAG_COEFFICIENT * v["averagescale"] ** Decimal(2))),
    StatDef("fallproof",               "Fallproof",                     lambda s: f"""{s['nickname'].value} {'is' if s['fallproof'].value else "isn't"} fallproof.""",  lambda s: CHK_Y if s['fallproof'].value else CHK_N,                                         is_shown=False,                                          requires=["terminalvelocity"],                      type=bool,                              value=lambda v: v["terminalvelocity"] < FALL_LIMIT),
    StatDef("fallprooficon",           "Fallproof Icon",                lambda s: CHK_Y if s['fallproof'] else CHK_N,                                       lambda s: CHK_Y if s['fallproof'].value else CHK_N,                                                     is_shown=False,                                          requires=["fallproof"],                             type=str,                               value=lambda v: emojis.voteyes if v["fallproof"] else emojis.voteno),
    StatDef("width",                   "Width",                         "{nickname} is **{width:,.3mu}** wide.",                                            "{width:,.3mu}",                                                                                        is_shown=False,                                          requires=["height"],                    power=1,    type=SV,                                value=lambda v: v["height"] * Decimal(4 / 17)),
    StatDef("soundtraveltime",         "Sound Travel Time",             "It would take sound **{soundtraveltime:,.3}** to travel {nickname}'s height.",     "{soundtraveltime:,.3mu}",                                                                              is_shown=False,                                          requires=["height"],                    power=1,    type=TV,                                value=lambda v: v["height"] * ONE_SOUNDSECOND),
    StatDef("lighttraveltime",         "Light Travel Time",             "It would take light **{lighttraveltime:,.3}** to travel {nickname}'s height.",     "{lighttraveltime:,.3mu}",                                                                              is_shown=False,                                          requires=["height"],                    power=1,    type=TV,                                value=lambda v: v["height"] * ONE_LIGHTSECOND),
    StatDef("caloriesneeded",          "Calories Needed",               "{nickname} needs **{caloriesneeded:,.0d}** calories per day.",                     "{caloriesneeded:,.0d}",                                                                                is_shown=False,                                                                                  power=3,    type=Decimal,                           value=lambda v: AVERAGE_CAL_PER_DAY),
    StatDef("waterneeded",             "Water Needed",                  "{nickname} needs **{waterneeded:,.3mu}** of water per day.",                       "{waterneeded:,.3mu}",                                                                                  is_shown=False,                                                                                  power=3,    type=WV,                                value=lambda v: AVERAGE_WATER_PER_DAY),
    StatDef("layarea",                 "Lay Area",                      "{nickname} would cover **{layarea:,.3mu}** of area laying down.",                  "{layarea:,.3mu}",                                                                                      is_shown=False,                                          requires=["height", "width"],           power=2,    type=AV,                                value=lambda v: v["height"] * v["width"]),
    StatDef("footarea",                "Foot Area",                     "{nickname}'s foot would cover **{footarea:,.3mu}** of area.",                      "{footarea:,.3mu}",                                                                                     is_shown=False,                                          requires=["footlength", "footwidth"],   power=2,    type=AV,                                value=(lambda v: v["footlength"] * v["footwidth"]),                              tags=["foot"]),
    StatDef("fingertiparea",           "Fingertip Area",                "{nickname}'s fingertip would cover **{fingertiparea:,.3mu}** of area.",            "{fingertiparea:,.3mu}",                                                                                is_shown=False,                                          requires=["fingertiplength"],           power=2,    type=AV,                                value=(lambda v: v["fingertiplength"] * v["fingertiplength"]),                   tags=["hand"]),
    StatDef("shoesize",                "Shoe Size",                     "{nickname}'s shoe size is **{shoesize}**.",                                        "{shoesize}",                                                                                           is_shown=False,                                          requires=["footlength", "gender"],                  type=str,                               value=(lambda v: format_shoe_size(v["footlength"], v["gender"])),                tags=["foot"]),
    StatDef("visibility",              "Visibility",                    "You would need **{visibility}** to see {nickname}.",                               "*{nickname} would need {visibility} to be seen.*",                                                     is_shown=lambda s: s["scale"].value < 1,                 requires=["height"],                                type=str,                               value=lambda v: calcVisibility(v["height"])),
    StatDef("height+",                 lambda s: s['height'].title,     "", lambda s: f"{s['height'].body}" + f"\n*{s['scale'].body} scale*" + (f"\n*{s['visibility'].body}" if s['visibility'].is_shown else ""),          z=1,    tags=["height"]),
    StatDef("weight+", lambda s: s['weight'].title, "", lambda s: f"{s['weight'].body}" + f"\n*{s['cubescale'].body} scale*", z=2),
    StatDef("footlength+", lambda s: "[FOOTNAME] length", "", lambda s: f"{s['footlength'].body}" + f"\n({s['shoesize'].body})"),
    StatDef("simplespeeds+", "Speeds", "", lambda s: "\n".join(s[f].body for f in ["walkperhour", "runperhour", "climbperhour", "swimperhour"])),
    StatDef("speeds+", "Speeds", "", lambda s: "\n".join(s[f].body for f in ["walkperhour", "runperhour", "climbperhour", "crawlperhour", "swimperhour", "driveperhour", "spaceshipperhour"]), z=-2, inline=False),
    StatDef("bases+", "Character Bases", "", lambda s: f"{s['height'].body} | {s['weight'].body}", z=-1)
]


def generate_statmap() -> dict[str, str]:
    statmap = {}
    for stat in all_stats:
        statmap[stat.key] = stat.key
    for statkey, aliases in stataliases.items():
        if statkey not in statmap:
            raise Exception(f"Alias for unrecognized stat: {statkey}")
        for alias in aliases:
            statmap[alias] = statkey
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
