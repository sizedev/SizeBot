# &change <DIFF | RATE | LIMITED_RATE>

## DIFF =
# SV
# +SV
# plus SV
# add SV
# -SV
# minus SV
# subtract SV
# sub SV
# 50%
# %50
# *2
# x2
# 2x
# /2
# **2

## RATE=
# DIFF/m
# DIFF/s
# DIFF/3s
# DIFF / s
# DIFF per hour
# DIFF per 2 hours
# DIFF every hour

## LIMITED_RATE=
# RATE until 9hours
# RATE for 9hours
# RATE -> 9hours
# RATE until 10meters
# RATE for 10meters
# RATE -> 10meters

from __future__ import annotations
from typing import Literal, TypedDict, cast

import re

from sizebot.lib.errors import InvalidSizeValue, ParseError, ThisShouldNeverHappenException
from sizebot.lib.utils import regexbuild
from sizebot.lib.types import BotContext
from sizebot.lib.units import SV, TV, Decimal

add_prefixes = ["+", "add", "plus"]
subtract_prefixes = ["-", "sub", "subtract", "minus"]
multiply_prefixes = ["*", "x", "X", "mult", "multiply", "multiply by"]
multiply_suffixes = ["x", "X"]
divide_prefixes = ["/", "div", "divide", "divide by"]
percent_prefixes = ["%"]
percent_suffixes = ["%"]
power_prefixes = ["**", "^"]

valid_prefixes = regexbuild([add_prefixes, subtract_prefixes, multiply_prefixes, divide_prefixes, percent_prefixes, power_prefixes], capture = True)
valid_suffixes = regexbuild([multiply_suffixes, percent_suffixes], capture = True)

rate_interfixes = ["/", "per", "every", "p"]

valid_rate_interfixes = regexbuild(rate_interfixes, capture = True)

limited_rate_interfixes = ["until", "for", "->", "-->"]

valid_limited_rate_interfixes = regexbuild(limited_rate_interfixes, capture = True)

ChangeType = Literal["add", "multiply", "power"]


class DiffJSON(TypedDict):
    changetype: ChangeType
    amount: str


class RateJSON(TypedDict):
    diff: DiffJSON
    time: str


class LimitedRateJSON(TypedDict):
    rate: RateJSON
    stop: str
    stoptype: Literal["TV", "SV"]


# Change
class Diff:
    def __init__(self, changetype: ChangeType, amount: SV | Decimal):
        self.changetype: ChangeType = changetype
        self.amount: SV | Decimal = amount

    @classmethod
    def parse(cls, s: str) -> Diff:
        prefixmatch = valid_prefixes + r"\s*(.*)"
        suffixmatch = r"(.*)\s*" + valid_suffixes

        changetype: ChangeType | None = None
        amount: SV | Decimal | None = None

        if m := re.match(prefixmatch, s):
            prefix: str = m.group(1)
            value: str = m.group(2)
            if prefix in add_prefixes:
                changetype = "add"
                amount = SV.parse(value)
            elif prefix in subtract_prefixes:
                changetype = "add"
                amount = SV(-SV.parse(value))
            elif prefix in multiply_prefixes:
                changetype = "multiply"
                amount = Decimal(value)
            elif prefix in divide_prefixes:
                changetype = "multiply"
                amount = cast(Decimal, Decimal(1) / Decimal(value))
            elif prefix in percent_prefixes:
                changetype = "multiply"
                amount = cast(Decimal, Decimal(value) / Decimal(100))
            elif prefix in power_prefixes:
                changetype = "power"
                amount = Decimal(value)
        elif m := re.match(suffixmatch, s):
            value: str = m.group(1)
            suffix: str = m.group(2)
            if suffix in multiply_suffixes:
                changetype = "multiply"
                amount = Decimal(value)
            elif suffix in percent_suffixes:
                changetype = "multiply"
                amount = cast(Decimal, Decimal(value) / Decimal(100))
        else:
            changetype = "add"
            amount = SV.parse(s)

        if changetype is None or amount is None:
            raise ParseError(s, "Diff")

        return cls(changetype, amount)

    def toJSON(self) -> DiffJSON:
        return {
            "changetype": self.changetype,
            "amount":     str(self.amount)
        }

    def __str__(self) -> str:
        if self.changetype == "add":
            operator = "-" if self.amount < 0 else "+"
        elif self.changetype == "multiply":
            operator = "/" if self.amount < 0 else "x"
        elif self.changetype == "power":
            operator = "^"
        else:
            raise ValueError(f"Unrecognized changetype: {self.changetype}")
        amount = format(self.amount, ",.3mu") if self.changetype == "add" else format(self.amount, ".10")
        return f"{operator}{amount}"

    def __mul__(self, other: Decimal) -> Diff:
        if not isinstance(other, Decimal):
            return NotImplemented
        return Diff(self.changetype, cast(SV | Decimal, self.amount * other))

    def __truediv__(self, other: Decimal) -> Diff:
        if not isinstance(other, Decimal):
            return NotImplemented
        return Diff(self.changetype, cast(SV | Decimal, self.amount / other))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    @classmethod
    def fromJSON(cls, jsondata: DiffJSON) -> Diff:
        changetype = jsondata["changetype"]
        if changetype == "add":
            amount = SV(jsondata["amount"])
        else:
            amount = Decimal(jsondata["amount"])

        return cls(changetype, amount)

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> Diff:
        return cls.parse(argument)


# Change per Time
class Rate:
    def __init__(self, diff: Diff, time: TV):
        self.diff = diff
        self.time = time

    @property
    def addPerSec(self) -> SV:
        if self.diff.changetype != "add":
            return SV(0)
        return SV(cast(SV, self.diff.amount / self.time))

    @property
    def mulPerSec(self) -> Decimal:
        if self.diff.changetype != "multiply":
            return Decimal(1)
        return Decimal(cast(Decimal, self.diff.amount ** (1 / self.time)))

    @property
    def stopSV(self) -> SV | None:
        return None

    @property
    def stopTV(self) -> TV | None:
        return None

    @classmethod
    def parse(cls, s: str) -> Rate:
        diff = None
        time = None

        # speed hack
        s = s.replace("mph", "mi/hr").replace("kph", "km/hr")

        match = r"(.*)\s*" + valid_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise ParseError(s, "Rate")
        diff = Diff.parse(m.group(1))
        time = TV.parse(m.group(3))

        return cls(diff, time)

    def toJSON(self) -> RateJSON:
        return {
            "diff": self.diff.toJSON(),
            "time": str(self.time)
        }

    def __str__(self) -> str:
        return f"{self.diff} per {self.time}"

    def __mul__(self, other: Decimal) -> Rate:
        if not isinstance(other, Decimal):
            return NotImplemented
        return Rate(self.diff * other, self.time)

    def __truediv__(self, other: Decimal) -> Rate:
        if not isinstance(other, Decimal):
            return NotImplemented
        return Rate(self.diff / other, self.time)

    @classmethod
    def fromJSON(cls, jsondata: RateJSON) -> Rate:
        diff = Diff.fromJSON(jsondata["diff"])
        time = TV(jsondata["time"])
        return cls(diff, time)

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> Rate:
        return cls.parse(argument)


# Positive Linear Change per Time
class LinearRate(Rate):
    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> Rate:
        rate = cls.parse(argument)
        if rate.diff.changetype != "add":
            raise InvalidSizeValue(argument, "Rate")
            # raise ValueError("Invalid rate for speed parsing.")
        if rate.diff.amount < 0:
            raise InvalidSizeValue(argument, "Rate")
            # raise ValueError("Speed can not go backwards!")
        return rate


# Change per Time, with End
class LimitedRate:
    def __init__(self, rate: Rate, stop: SV | TV):
        self.rate = rate
        self.stop = stop

    @property
    def addPerSec(self) -> SV:
        return self.rate.addPerSec

    @property
    def mulPerSec(self) -> Decimal:
        return self.rate.mulPerSec

    @property
    def stopSV(self) -> SV | None:
        if not isinstance(self.stop, SV):
            return None
        return self.stop

    @property
    def stopTV(self) -> TV | None:
        if not isinstance(self.stop, TV):
            return None
        return self.stop

    @classmethod
    def parse(cls, s: str) -> LimitedRate:
        match = r"(.*)\s*" + valid_limited_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise ParseError(s, "LimitedRate")

        rate = Rate.parse(m.group(1))

        try:
            stop = SV.parse(m.group(3))
        except InvalidSizeValue:
            try:
                stop = TV.parse(m.group(3))
            except InvalidSizeValue:
                raise ParseError(s, "LimitedRate")

        return cls(rate, stop)

    def toJSON(self) -> LimitedRateJSON:
        stoptype = "SV" if isinstance(self.stop, SV) else "TV"
        return {
            "rate": self.rate.toJSON(),
            "stop": str(self.stop),
            "stoptype": stoptype
        }

    def __str__(self) -> str:
        joiner = "for" if isinstance(self.stop, TV) else "until"
        return f"{self.rate} {joiner} {self.stop}"

    @classmethod
    def fromJSON(cls, jsondata: LimitedRateJSON) -> LimitedRate:
        rate = Rate.fromJSON(jsondata["rate"])
        stoptype = jsondata["stoptype"]
        if stoptype == "SV":
            stop = SV(jsondata["stop"])
        elif stoptype == "TV":
            stop = TV(jsondata["stop"])
        else:
            raise ThisShouldNeverHappenException("")

        return cls(rate, stop)

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> LimitedRate:
        return cls.parse(argument)
