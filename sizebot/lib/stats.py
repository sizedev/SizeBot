from __future__ import annotations

from functools import cached_property
from typing import Any, Optional, TypeVar, Callable
import math

from sizebot.lib import errors
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, TV, WV, AV
from sizebot.lib.userdb import PlayerStats, DEFAULT_HEIGHT as average_height, DEFAULT_LIFT_STRENGTH, FALL_LIMIT
from sizebot.lib.shoesize import to_shoe_size
from sizebot.lib.surface import can_walk_on_water

DEFAULT_THREAD_THICKNESS = SV("0.001016")
AVERAGE_HEIGHT = average_height
AVERAGE_BREATHEPERHOUR = SV(720)
AVERAGE_WALKPERHOUR = SV(5630)
AVERAGE_RUNPERHOUR = SV(10729)
AVERAGE_SWIMPERHOUR = SV(3219)
AVERAGE_CLIMBPERHOUR = SV(330)
AVERAGE_CRAWLPERHOUR = SV(2556)
AVERAGE_DRIVEPERHOUR = SV(96561)
AVERAGE_SPACESHIPPERHOUR = SV(3600 * 1000)
WALKSTEPSPERHOUR = SV(900)
RUNSTEPSPERHOUR = SV(10200)
ONE_SOUNDSECOND = SV(340.27)
ONE_LIGHTSECOND = SV(299792000)
AVERAGE_CAL_PER_DAY = 2000
AVERAGE_WATER_PER_DAY = WV(3200)
AVERAGE_HUMAN_DRAG_COEFFICIENT = Decimal("1.123")
GRAVITY = Decimal("9.807")  # m/s^2
AIR_DENSITY = Decimal("1.204")  # kg/m3

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


T = TypeVar("T")


def wrap_type(f: Callable[[Any], T] | None) -> Callable[[Any], T | None]:
    if f is None:
        def default_func(v):
            return v
        f = default_func

    def wrapped(v: any) -> T | None:
        if v is None:
            return None
        return f(v)
    return wrapped


class StatDef:
    def __init__(self,
                 key: str,
                 *,
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
                 inline: bool = True,
                 aliases: list[str] = None
                 ):
        if userkey is not None and power is None:
            raise Exception(f'StatDef("{key}") with userkey must have power set')
        self.key = key
        self.get_title = wrap_str(title)
        self.get_body = wrap_str(body)
        self.get_string = wrap_str(string)
        self.get_is_shown = wrap_bool(is_shown)
        self.userkey = userkey
        self.get_value = value
        self.requires = requires or []
        self.power = power
        self.type = wrap_type(type)
        self.orderkey = grouped_z(z)
        self.tags = tags or []
        self.inline = inline
        self.aliases = aliases or []

    def load_stat(self,
                  sb: StatBox,
                  values: dict[str, Any],
                  *,
                  userstats: PlayerStats
                  ) -> None | Stat:

        is_setbyuser = False
        value = None
        if self.userkey is not None and self.get_value is not None:
            # try to load from userstats
            value = userstats.get(self.userkey, None)
            if value is not None:
                is_setbyuser = True
            else:
                # else calculate from value()
                value = self.get_value(values)
        elif self.userkey is not None:
            # load from userstats
            value = userstats[self.userkey]
            if value is not None:
                is_setbyuser = True
        elif self.get_value is not None:
            # calculate from value()
            if any(r not in values for r in self.requires):
                return
            value = self.get_value(values)
        else:
            value = None

        return Stat(sb, self, self.type(value), is_setbyuser)

    def scale_stat(self,
                   sb: StatBox,
                   values: dict[str, Any],
                   *,
                   scale: Decimal = 1,
                   old_value: Any = None,
                   is_setbyuser: bool
                   ) -> None | Stat:
        value = None
        if self.userkey is None and self.get_value is None:
            # Can't scale without userkey or get_value
            value = None
        elif self.power is not None:
            if old_value is None:
                value = None
            elif self.power == 0:
                # Just use the old value
                value = old_value
            else:
                # Scale by the power
                value = old_value * (scale ** self.power)
        else:
            # calculate from value()
            if any(r not in values for r in self.requires):
                return
            value = self.get_value(values)

        return Stat(sb, self, self.type(value), is_setbyuser)


class Stat:
    def __init__(self, sb: StatBox, definition: StatDef, value: Any, is_setbyuser: bool):
        self.sb = sb
        self.definition = definition
        self.value = value
        self.is_setbyuser = is_setbyuser

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
            result = sdef.load_stat(sb, values, userstats=userstats)
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
            result = s.definition.scale_stat(sb, values, scale=scale_value, old_value=s.value, is_setbyuser=s.is_setbyuser)
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


def bool_to_icon(value):
    CHK_Y = "✅"
    CHK_N = "❎"
    if value:
        return CHK_Y
    else:
        return CHK_N


all_stats = [
    StatDef("nickname",
            title="Nickname",
            string="{nickname}",
            body="{nickname}",
            is_shown=False,
            type=str,
            power=0,
            userkey="nickname"),
    StatDef("scale",
            title="Scale",
            string=lambda s: format_scale(s['scale'].value),
            body=lambda s: format_scale(s['scale'].value),
            type=Decimal,
            power=1,
            value=lambda v: 1),
    StatDef("viewscale",
            title="Viewscale",
            string=lambda s: format_scale(s['viewscale'].value),
            body=lambda s: format_scale(s['viewscale'].value),
            is_shown=False,
            requires=["scale"],
            type=Decimal,
            value=lambda v: 1 / v["scale"]),
    StatDef("squarescale",
            title="Square Scale",
            string=lambda s: format_scale(s['squarescale'].value),
            body=lambda s: format_scale(s['squarescale'].value),
            is_shown=False,
            requires=["scale"],
            power=2,
            type=Decimal,
            value=lambda v: v["scale"] ** 2),
    StatDef("cubescale",
            title="Cube Scale",
            string=lambda s: format_scale(s['cubescale'].value),
            body=lambda s: format_scale(s['cubescale'].value),
            is_shown=False,
            requires=["scale"],
            power=3,
            type=Decimal,
            value=lambda v: v["scale"] ** 3),
    StatDef("height",
            title="Height",
            string="{nickname}'s current height is **{height:,.3mu}**, or {scale} scale.",
            body="{height:,.3mu}",
            is_shown=False,
            power=1,
            type=SV,
            userkey="height",
            tags=["keypoint"],
            aliases=["size"]),
    StatDef("weight",
            title="Weight",
            string="{nickname}'s current weight is **{weight:,.3mu}**.",
            body="{weight:,.3mu}",
            is_shown=False,
            power=3,
            type=WV,
            userkey="weight",
            aliases=["mass"]),
    StatDef("gender",
            title="Gender",
            string="{nickname}'s gender is {gender}.",
            body="{gender}",
            is_shown=False,
            power=0,
            type=str,
            userkey="gender"),  # TODO: Should this be autogender?
    StatDef("averagescale",
            title="Average Scale",
            string="{nickname} is {averagescale} times taller than an average person.",
            body="{averagescale}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=Decimal,
            value=lambda v: v["height"] / AVERAGE_HEIGHT),
    StatDef("hairlength",
            title="{hairname} Length",
            string=lambda s: f"{s['nickname'].value}'s {s['hairname'].value.lower()} is **{s['hairlength'].value:,.3mu}** long.",
            body="{hairlength:,.3mu}",
            is_shown=lambda s: s["hairlength"].value,
            power=1,
            type=SV,
            userkey="hairlength"),
    StatDef("taillength",
            title="Tail Length",
            string="{nickname}'s tail is **{taillength:,.3mu}** long.",
            body="{taillength:,.3mu}",
            is_shown=lambda s: s["taillength"].value,
            power=1,
            type=SV,
            userkey="taillength",
            tags=["furry"],
            aliases=["tail"]),
    StatDef("earheight",
            title="Ear Height",
            string="{nickname}'s ear is **{earheight:,.3mu}** tall.",
            body="{earheight:,.3mu}",
            is_shown=lambda s: s["earheight"].value,
            power=1,
            type=SV,
            userkey="earheight",
            tags=["furry"],
            aliases=["ear"]),
    StatDef("footlength",
            title="{footname} Length",
            string=lambda s: f"{s['nickname'].value}'s {s['footname'].value.lower()} is **{s['footlength'].value:,.3mu}** long.",
            body="{footlength:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            userkey="footlength",
            value=lambda v: v["height"] / 7,
            tags=["foot"],
            aliases=["foot", "feet", "paw", "paws"]),
    StatDef("liftstrength",
            title="Lift Strength",
            string="{nickname} can lift {liftstrength:,.3mu}.",
            body="{liftstrength:,.3mu}",
            requires=["height"],
            power=3,
            type=WV,
            userkey="liftstrength",
            value=lambda v: DEFAULT_LIFT_STRENGTH,
            aliases=["strength", "lift", "carry", "carrystrength"]),
    StatDef("footwidth",
            title="{footname} Width",
            string=lambda s: f"{s['nickname'].value}'s {s['footname'].value.lower()} is **{s['footwidth'].value:,.3mu}** wide.",
            body="{footwidth:,.3mu}",
            requires=["footlength"],
            power=1,
            type=SV,
            value=(lambda v: v["footlength"] * Decimal(2 / 3)),
            tags=["foot"]),
    StatDef("shoeprintdepth",
            title="Shoeprint Depth",
            string="{nickname}'s shoeprint is **{shoeprintdepth:,.3mu}** deep.",
            body="{shoeprintdepth:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] / 135,
            aliases=["shoeprint", "footprint"]),
    StatDef("pointerlength",
            title="Pointer Finger Length",
            string="{nickname}'s pointer finger is **{pointerlength:,.3mu}** long.",
            body="{pointerlength:,.3mu}",
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / Decimal(17.26)),
            tags=["hand"],
            aliases=["finger", "pointer"]),
    StatDef("thumbwidth",
            title="Thumb Width",
            string="{nickname}'s thumb is **{thumbwidth:,.3mu}** wide.",
            body="{thumbwidth:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / Decimal(69.06)),
            tags=["hand"],
            aliases=["thumb"]),
    StatDef("fingertiplength",
            title="Fingertip Length",
            string="{nickname}'s fingertip is **{fingertiplength:,.3mu}** long.",
            body="{fingertiplength:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / Decimal(95.95)),
            tags=["hand"],
            aliases=["fingertip"]),
    StatDef("fingerprintdepth",
            title="Fingerprint Depth",
            string="{nickname}'s fingerprint is **{fingerprintdepth:,.3mu}** deep.",
            body="{fingerprintdepth:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / 35080),
            tags=["hand"],
            aliases=["fingerprint"]),
    StatDef("threadthickness",
            title="Thread Thickness",
            string="{nickname}'s clothing threads are **{threadthickness:,.3mu}** thick.",
            body="{threadthickness:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_LARGE,
            power=1,
            type=SV,
            value=lambda v: DEFAULT_THREAD_THICKNESS,
            aliases=["thread"]),
    StatDef("hairwidth",
            title="{hairname} Width",
            string=lambda s: f"{s['nickname'].value}'s {s['hairname'].value.lower()} is **{s['hairwidth'].value:,.3mu}** wide.",
            body="{hairwidth:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] / 23387),
    StatDef("nailthickness",
            title="Nail Thickness",
            string="{nickname}'s nails are **{nailthickness:,.3mu}** thick.",
            body="{nailthickness:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / 2920),
            tags=["hand"],
            aliases=["nail", "fingernail"]),
    StatDef("eyewidth",
            title="Eye Width",
            string="{nickname}'s eyes are **{eyewidth:,.3mu}** wide.",
            body="{eyewidth:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] / Decimal(73.083),
            aliases=["eye", "eyes"]),
    StatDef("jumpheight",
            title="Jump Height",
            string="{nickname} can jump **{jumpheight:,.3mu}** high.",
            body="{jumpheight:,.3mu}",
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] / Decimal(3.908),
            aliases=["jump"]),
    StatDef("averagelookangle",
            title="Average Look Angle",
            string="{nickname} would have to look {averagelookangle} to see the average person.",
            body="{averagelookangle}",
            is_shown=False,
            requires=["height"],
            type=Decimal,
            value=lambda v: abs(calcViewAngle(v["height"], AVERAGE_HEIGHT))),
    StatDef("averagelookdirection",
            title="Average Look Direction",
            string="...",
            body="{averagelookdirection}",
            is_shown=False,
            requires=["height"],
            type=str,
            value=lambda v: "up" if calcViewAngle(v["height"], AVERAGE_HEIGHT) >= 0 else "down"),
    StatDef("walkperhour",
            title="Walk Per Hour",
            string="{nickname} walks **{walkperhour:,.3mu} per hour**.",
            body=emojis.walk + "{walkperhour:,.1M} per hour / {walkperhour:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_WALKPERHOUR * v["averagescale"]),
            tags=["movement"],
            aliases=["walk", "speed", "step"]),
    StatDef("breathewindspeed",
            title="Breathe Wind Speed",
            string="{nickname}'s breath is **{breathewindspeed:,.3mu} per hour**.",
            body="{breathewindspeed:,.1M} per hour / {breathewindspeed:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_BREATHEPERHOUR * v["averagescale"]),
            aliases=["breath", "breathe", "wind"]),
    StatDef("runperhour",
            title="Run Per Hour",
            string="{nickname} runs **{runperhour:,.3mu} per hour**.",
            body=emojis.run + " {runperhour:,.1M} per hour / {runperhour:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_RUNPERHOUR * v["averagescale"]),
            tags=["movement"],
            aliases=["run"]),
    StatDef("swimperhour",
            title="Swim Per Hour",
            string="{nickname} swims **{swimperhour:,.3mu} per hour**.",
            body=emojis.swim + " {swimperhour:,.1M} per hour / {swimperhour:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_SWIMPERHOUR * v["averagescale"]),
            tags=["movement"],
            aliases=["swim", "stroke"]),
    StatDef("climbperhour",
            title="Climb Per Hour",
            string="{nickname} climbs **{climbperhour:,.3mu} per hour**.",
            body=emojis.climb + " {climbperhour:,.1M} per hour / {climbperhour:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_CLIMBPERHOUR * v["averagescale"]),
            tags=["movement"],
            aliases=["climb", "pull"]),
    StatDef("crawlperhour",
            title="Crawl Per Hour",
            string="{nickname} crawls **{crawlperhour:,.3mu} per hour**.",
            body=emojis.crawl + " {crawlperhour:,.1M} per hour / {crawlperhour:,.1U} per hour",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_CRAWLPERHOUR * v["averagescale"]),
            tags=["movement"],
            aliases=["crawl"]),
    StatDef("driveperhour",
            title="Drive Per Hour",
            string="{nickname} drives **{driveperhour:,.3mu} per hour**.",
            body=emojis.drive + " {driveperhour:,.1M} per hour / {driveperhour:,.1U} per hour",
            is_shown=False,
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_DRIVEPERHOUR),
            tags=["movement"],
            aliases=["drive"]),
    StatDef("spaceshipperhour",
            title="Spaceship Per Hour",
            string="{nickname} flys at spaceship at **{spaceshipperhour:,.3mu} per hour**.",
            body=emojis.spaceship + " {spaceshipperhour:,.1M} per hour / {spaceshipperhour:,.1U} per hour",
            is_shown=False,
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_SPACESHIPPERHOUR),
            tags=["movement"]),
    StatDef("walksteplength",
            title="Walk Step Length",
            string="{nickname} takes **{walksteplength:,.3mu}** strides while walking.",
            body="{walksteplength:,.3mu}",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_WALKPERHOUR * v["averagescale"] / WALKSTEPSPERHOUR),
            tags=["movement"]),
    StatDef("runsteplength",
            title="Run Step Length",
            string="{nickname} takes **{runsteplength:,.3mu}** strides while runing.",
            body="{runsteplength:,.3mu}",
            is_shown=False,
            requires=["averagescale"],
            power=1,
            type=SV,
            value=(lambda v: AVERAGE_RUNPERHOUR * v["averagescale"] / RUNSTEPSPERHOUR),
            tags=["movement"]),
    StatDef("climbsteplength",
            title="Climb Step Length",
            string="{nickname} takes **{climbsteplength:,.3mu}** strides while climbing.",
            body="{climbsteplength:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] * Decimal(1 / 2.5)),
            tags=["movement"]),
    StatDef("crawlsteplength",
            title="Crawl Step Length",
            string="{nickname} takes **{crawlsteplength:,.3mu}** strides while crawling.",
            body="{crawlsteplength:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] * Decimal(1 / 2.577)),
            tags=["movement"]),
    StatDef("swimsteplength",
            title="Swim Step Length",
            string="{nickname} takes **{swimsteplength:,.3mu}** strides while swiming.",
            body="{swimsteplength:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] * Decimal(6 / 7)),
            tags=["movement"]),
    StatDef("horizondistance",
            title="View Distance to Horizon",
            string="{nickname} can see **{horizondistance:,.3mu}** to the horizon.",
            body="{horizondistance:,.3mu}",
            is_shown=False,
            requires=["height"],
            type=SV,
            value=lambda v: calcHorizon(v["height"]),
            aliases=["horizon"]),
    StatDef("dragcoefficient",
            title="Drag Coefficient",
            string="{nickname}'s drag coefficient is {dragcoefficient}",
            body="{dragcoefficient}",
            is_shown = False,
            requires=["averagescale"],
            type=Decimal,
            value=lambda v: AVERAGE_HUMAN_DRAG_COEFFICIENT * v["averagescale"] ** Decimal(2)),
    StatDef("terminalvelocity",
            title="Terminal Velocity",
            string="{nickname}'s terminal velocity is **{terminalvelocity:,.3mu} per hour.**",
            body=lambda s: f"{s['terminalvelocity'].value:,.1M} per second\n({s['terminalvelocity'].value:,.1U} per second)" + ("\n*This user can safely fall from any height.*" if s["fallproof"].value else ""),
            requires=["weight", "dragcoefficient"],
            type=SV,
            value=lambda v: math.sqrt((2 * GRAVITY * (v["weight"] / 1000)) / (v["dragcoefficient"] * AIR_DENSITY)),
            aliases=["velocity", "fall"]),
    StatDef("fallproof",
            title="Fallproof",
            string=lambda s: f"""{s['nickname'].value} {'is' if s['fallproof'].value else "isn't"} fallproof.""",
            body=lambda s: bool_to_icon(s['fallproof'].value),
            is_shown=False,
            requires=["terminalvelocity"],
            type=bool,
            value=lambda v: v["terminalvelocity"] < FALL_LIMIT),
    StatDef("fallprooficon",
            title="Fallproof Icon",
            string=lambda s: bool_to_icon(s['fallproof']),
            body=lambda s: bool_to_icon(s['fallproof'].value),
            is_shown=False,
            requires=["fallproof"],
            type=str,
            value=lambda v: emojis.voteyes if v["fallproof"] else emojis.voteno),
    StatDef("width",
            title="Width",
            string="{nickname} is **{width:,.3mu}** wide.",
            body="{width:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(4 / 17)),
    StatDef("soundtraveltime",
            title="Sound Travel Time",
            string="It would take sound **{soundtraveltime:,.3}** to travel {nickname}'s height.",
            body="{soundtraveltime:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=TV,
            value=lambda v: v["height"] * ONE_SOUNDSECOND,
            aliases=["sound"]),
    StatDef("lighttraveltime",
            title="Light Travel Time",
            string="It would take light **{lighttraveltime:,.3}** to travel {nickname}'s height.",
            body="{lighttraveltime:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=TV,
            value=lambda v: v["height"] * ONE_LIGHTSECOND,
            aliases=["light"]),
    StatDef("caloriesneeded",
            title="Calories Needed",
            string="{nickname} needs **{caloriesneeded:,.0d}** calories per day.",
            body="{caloriesneeded:,.0d}",
            is_shown=False,
            power=3,
            type=Decimal,
            value=lambda v: AVERAGE_CAL_PER_DAY,
            aliases=["calories"]),
    StatDef("waterneeded",
            title="Water Needed",
            string="{nickname} needs **{waterneeded:,.3mu}** of water per day.",
            body="{waterneeded:,.3mu}",
            is_shown=False,
            power=3,
            type=WV,
            value=lambda v: AVERAGE_WATER_PER_DAY,
            aliases=["water"]),
    StatDef("layarea",
            title="Lay Area",
            string="{nickname} would cover **{layarea:,.3mu}** of area laying down.",
            body="{layarea:,.3mu}",
            is_shown=False,
            requires=["height", "width"],
            power=2,
            type=AV,
            value=lambda v: v["height"] * v["width"],
            aliases=["lay"]),
    StatDef("footarea",
            title="{footname} Area",
            string=lambda s: f"{s['nickname'].value}'s {s['footname'].value.lower()} would cover **{s['footarea'].value:,.3mu}** of area.",
            body="{footarea:,.3mu}",
            is_shown=False,
            requires=["footlength", "footwidth"],
            power=2,
            type=AV,
            value=(lambda v: v["footlength"] * v["footwidth"]),
            tags=["foot"]),
    StatDef("fingertiparea",
            title="Fingertip Area",
            string="{nickname}'s fingertip would cover **{fingertiparea:,.3mu}** of area.",
            body="{fingertiparea:,.3mu}",
            is_shown=False,
            requires=["fingertiplength"],
            power=2,
            type=AV,
            value=(lambda v: v["fingertiplength"] * v["fingertiplength"]),
            tags=["hand"]),
    StatDef("shoesize",
            title="Shoe Size",
            string="{nickname}'s shoe size is **{shoesize}**.",
            body="{shoesize}",
            is_shown=False,
            requires=["footlength", "gender"],
            type=str,
            value=(lambda v: to_shoe_size(v["footlength"], v["gender"])),
            tags=["foot"],
            aliases=["shoe", "shoes"]),
    StatDef("visibility",
            title="Visibility",
            string="You would need **{visibility}** to see {nickname}.",
            body="*{nickname} would need {visibility} to be seen.*",
            is_shown=lambda s: s["scale"].value < 1,
            requires=["height"],
            type=str,
            value=lambda v: calcVisibility(v["height"]),
            aliases=["visible", "see"]),
    StatDef("eyeheight",
            title="Eye Height",
            string="{nickname}'s eye is **{eyeheight:,.3mu}** high.",
            body="{eyeheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.936),
            tags=["keypoint"]),
    StatDef("neckheight",
            title="Neck Height",
            string="{nickname}'s neck is **{neckheight:,.3mu}** high.",
            body="{neckheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.870),
            tags=["keypoint"],
            aliases=["neck"]),
    StatDef("shoulderheight",
            title="Shoulder Height",
            string="{nickname}'s shoulder is **{shoulderheight:,.3mu}** high.",
            body="{shoulderheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.818),
            tags=["keypoint"],
            aliases=["shoulder"]),
    StatDef("chestheight",
            title="Chest Height",
            string="{nickname}'s chest is **{chestheight:,.3mu}** high.",
            body="{chestheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.720),
            tags=["keypoint"],
            aliases=["chest"]),
    StatDef("waistheight",
            title="Waist Height",
            string="{nickname}'s waist is **{waistheight:,.3mu}** high.",
            body="{waistheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.530),
            tags=["keypoint"],
            aliases=["waist"]),
    StatDef("thighheight",
            title="Thigh Height",
            string="{nickname}'s thigh is **{thighheight:,.3mu}** high.",
            body="{thighheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.485),
            tags=["keypoint"],
            aliases=["thigh"]),
    StatDef("kneeheight",
            title="Knee Height",
            string="{nickname}'s knee is **{kneeheight:,.3mu}** high.",
            body="{kneeheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] * Decimal(0.285),
            tags=["keypoint"],
            aliases=["knee"]),
    StatDef("ankleheight",
            title="Ankle Height",
            string="{nickname}'s ankle is **{ankleheight:,.3mu}** high.",
            body="{ankleheight:,.3mu}",
            is_shown=False,
            requires=["height"],
            power=1,
            type=SV,
            value=lambda v: v["height"] / 17,
            tags=["keypoint"],
            aliases=["ankle"]),
    StatDef("toeheight",
            title="Toe Height",
            string="{nickname}'s toe is **{toeheight:,.3mu}** thick.",
            body="{toeheight:,.3mu}",
            is_shown=lambda s: s["scale"].value > IS_VERY_LARGE,
            requires=["height"],
            power=1,
            type=SV,
            value=(lambda v: v["height"] / 65),
            tags=["keypoint"],
            aliases=["toe", "toes"]),
    StatDef("height+",
            title=lambda s: s['height'].title,
            string="",
            body=lambda s: f"{s['height'].body}" + f"\n*{s['scale'].body} scale*" + (f"\n{s['visibility'].body}" if s['visibility'].is_shown else ""),
            z=1),
    StatDef("weight+",
            title=lambda s: s['weight'].title,
            string="",
            body=lambda s: f"{s['weight'].body}" + f"\n*{s['cubescale'].body} scale*",
            z=2),
    StatDef("footlength+",
            title="{footname} Length",
            string="",
            body=lambda s: f"{s['footlength'].body}" + f"\n({s['shoesize'].body})",
            z=3),
    StatDef("simplespeeds+",
            title="Speeds",
            string="",
            body=lambda s: "\n".join(s[f].body for f in ["walkperhour", "runperhour", "climbperhour", "swimperhour"]),
            z=-2,
            inline=False),
    StatDef("speeds+",
            title="Speeds",
            string="",
            body=lambda s: "\n".join(s[f].body for f in ["walkperhour", "runperhour", "climbperhour", "crawlperhour", "swimperhour", "driveperhour", "spaceshipperhour"]),
            is_shown = False),
    StatDef("bases+",
            title="Character Bases",
            string="",
            body=lambda s: f"{s['height'].body} | {s['weight'].body}",
            z=-1),
    StatDef("pawtoggle",
            title="Paw Toggle",
            string="{nickname}'s paw toggle is {pawtoggle}.",
            body=lambda s: bool_to_icon(s['pawtoggle'].value),
            is_shown=False,
            type=bool,
            power=0,
            userkey="pawtoggle"),
    StatDef("furtoggle",
            title="Fur Toggle",
            string="{nickname}'s fur toggle is {furtoggle}.",
            body=lambda s: bool_to_icon(s['furtoggle'].value),
            is_shown=False,
            type=bool,
            power=0,
            userkey="furtoggle"),
    StatDef("footname",
            title="Foot Name",
            string="{nickname}'s foot name is {footname}.",
            body="{footname}",
            is_shown=False,
            type=str,
            value=lambda v: "Paw" if v["pawtoggle"] else "Foot"),
    StatDef("hairname",
            title="Hair Name",
            string="{nickname}'s hair name is {hairname}.",
            body="{hairname}",
            is_shown=False,
            type=str,
            value=lambda v: "Fur" if v["furtoggle"] else "Hair"),
    StatDef("walkonwater",
            title="Can Walk On Water",
            string=lambda s: f"""{s['nickname'].value} {'can' if s['walkonwater'].value else "can't"} walk on water.""",
            body=lambda s: bool_to_icon(s['walkonwater'].value),
            requires=["weight", "footlength", "footwidth"],
            type=bool,
            is_shown=False,
            value=lambda v: can_walk_on_water(v["weight"], v["footlength"], v["footwidth"]),
            aliases=["surfacetension", "tension", "float"]),
    StatDef("blowoverspeed",
            title="Wind Speed to Blow Over",
            string=lambda s: f"""{s['nickname'].value} would blow over from {s['blowoverspeed'].value} per hour wind.""",
            body=lambda s: f"{s['blowoverspeed'].value} per hour",
            requires=["height", "width", "weight"],
            type=SV,
            is_shown=False,
            value=lambda v: SV(math.sqrt((v["weight"] * GRAVITY) / (v["height"] * v["width"] * AIR_DENSITY)) * 60 * 60),
            aliases=["blow"])
]


def generate_statmap() -> dict[str, str]:
    statmap = {}
    # Load all keys
    for stat in all_stats:
        if stat.key in statmap:
            raise Exception(f"Duplicate key: {stat.key}")
        statmap[stat.key] = stat.key
    # Load all aliases
    for stat in all_stats:
        for alias in stat.aliases:
            if alias in statmap:
                raise Exception(f"Duplicate alias: {alias}")
            statmap[alias] = stat.key
    return statmap


def generate_taglist() -> list[str]:
    tags = []
    for stat in all_stats:
        if stat.tags:
            tags.extend(stat.tags)
    tags = list(set(tags))
    return tags


statmap = generate_statmap()
taglist = generate_taglist()


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


# TODO: CamelCase
def calcHorizon(height: SV) -> SV:
    EARTH_RADIUS = 6378137
    return SV(math.sqrt((EARTH_RADIUS + height) ** 2 - EARTH_RADIUS ** 2))


# TODO: CamelCase
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
