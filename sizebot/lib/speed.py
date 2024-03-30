from __future__ import annotations

import math

from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.shoesize import to_shoe_size
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.utils import pretty_time_delta


class Movement:
    def __init__(self, key: str, dist: SV, *, stats: StatBox, showspeed: bool, steps: str = None, always_active: bool = False):
        self.key = key
        self.stepname = steps
        self.always_active = always_active
        self.stats = stats
        self.dist = dist
        self.showspeed = showspeed

    @property
    def perhour(self) -> SV:
        perhourkey = f"{self.key}perhour"
        return self.stats[perhourkey].value

    @property
    def steplength(self) -> SV:
        if not self.stepname:
            return
        steplengthkey = f"{self.key}steplength"
        return self.stats[steplengthkey].value

    @property
    def seconds_to_travel(self) -> Decimal:
        return (self.dist / self.perhour) * 60 * 60

    @property
    def steps_to_travel(self) -> int:
        if not self.stepname:
            return
        return math.ceil(self.dist / self.steplength)

    @property
    def emoji(self) -> str:
        return emojis[self.key]

    @property
    def is_active(self) -> bool:
        if self.always_active:
            return True
        return self.seconds_to_travel > 1

    @property
    def pretty_time_to_travel(self) -> str:
        return pretty_time_delta(self.seconds_to_travel, roundeventually=True)

    @property
    def pretty_steps_to_travel(self) -> str:
        return f" {self.steps_to_travel:,.3} {self.stepname}" if self.stepname else ""

    @property
    def pretty_speed(self) -> str:
        return f"\n*{emojis['blank']}{self.perhour:,.3mu} per hour*" if self.showspeed else ""

    @property
    def string(self):
        return f"{self.emoji} {self.pretty_time_to_travel}{self.pretty_steps_to_travel}{self.pretty_speed}"


def speedcalc(traveller: StatBox, dist: SV, *, speed = False, foot = False, include_relative = False):
    movements = [
        Movement("walk",      dist, stats=traveller, showspeed=speed, stepname="steps", always_active=True),
        Movement("run",       dist, stats=traveller, showspeed=speed, stepname="strides"),
        Movement("climb",     dist, stats=traveller, showspeed=speed, stepname="pulls", always_active=True),
        Movement("crawl",     dist, stats=traveller, showspeed=speed, stepname="steps"),
        Movement("swim",      dist, stats=traveller, showspeed=speed, stepname="strokes"),
        Movement("drive",     dist, stats=traveller, showspeed=speed),
        Movement("spaceship", dist, stats=traveller, showspeed=speed)
    ]

    out = f"{emojis['ruler']} {dist:,.3mu}"
    if foot:
        out += f" ({to_shoe_size(dist, 'm')})"
    out += "\n"
    if include_relative:
        reldist = SV(dist * traveller["viewscale"].value)
        out += f"{emojis['eyes']} {reldist:,.3mu}\n"
        if foot:
            out += f"{emojis['blank']} ({to_shoe_size(reldist, 'm')})\n"
    out += "\n".join(m.string for m in movements if m.is_active)

    return out
