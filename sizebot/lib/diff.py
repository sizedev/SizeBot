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
from typing import Literal, Any

import re

from discord.ext import commands

from sizebot.lib.errors import InvalidSizeValue, ParseError, ThisShouldNeverHappenException
from sizebot.lib.utils import regexbuild, try_or_none
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, TV

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


class Diff:
    def __init__(self, original: str, changetype: Literal["add", "multiply", "power"], amount: SV | Decimal):
        self.changetype = changetype
        self.amount = amount
        self.original = original

    @classmethod
    def parse(cls, s: str) -> Diff:
        prefixmatch = valid_prefixes + r"\s*(.*)"
        suffixmatch = r"(.*)\s*" + valid_suffixes

        ct = None
        v = None

        if m := re.match(prefixmatch, s):
            prefix = m.group(1)
            value = m.group(2)

            if prefix in add_prefixes:
                ct = "add"
                v = SV.parse(value)
            elif prefix in subtract_prefixes:
                ct = "add"
                v = SV.parse(value) * -1
            elif prefix in multiply_prefixes:
                ct = "multiply"
                v = Decimal(value)
            elif prefix in divide_prefixes:
                ct = "multiply"
                v = Decimal(1) / Decimal(value)
            elif prefix in percent_prefixes:
                ct = "multiply"
                v = Decimal(value) / Decimal(100)
            elif prefix in power_prefixes:
                ct = "power"
                v = Decimal(value)

        elif m := re.match(suffixmatch, s):
            value = m.group(1)
            suffix = m.group(2)

            if suffix in multiply_suffixes:
                ct = "multiply"
                v = Decimal(value)
            elif suffix in percent_suffixes:
                ct = "multiply"
                v = Decimal(value) / Decimal(100)

        else:
            ct = "add"
            v = SV.parse(s)

        return cls(s, ct, v)

    def toJSON(self) -> Any:
        return {
            "changetype": self.changetype,
            "amount":     str(self.amount),
            "original":   self.original
        }

    def __str__(self) -> str:
        operator: str = ""
        amount: str = ""
        if self.changetype == "add":
            operator = "-" if self.amount < 0 else "+"
        elif self.changetype == "multiply":
            operator = "/" if self.amount < 0 else "x"
        elif self.changetype == "power":
            operator = "^"
        amount = format(self.amount, ",.3mu") if self.changetype == "add" else format(self.amount, ".10")
        return f"{operator}{amount}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    @classmethod
    def fromJSON(cls, jsondata: Any) -> Diff:
        changetype = jsondata["changetype"]
        if changetype == "add":
            amount = SV(jsondata["amount"])
        else:
            amount = Decimal(jsondata["amount"])
        original = jsondata["original"]

        return cls(original, changetype, amount)

    @classmethod
    async def convert(cls, ctx: commands.Context[commands.Bot], argument: str) -> Diff:
        return cls.parse(argument)


class Rate:
    def __init__(self, original: str, diff: Diff, time: TV):
        self.diff = diff
        self.time = time
        self.original = original

    @classmethod
    def parse(cls, s: str) -> Rate:
        d = None
        t = None

        # speed hack
        s = s.replace("mph", "mi/hr").replace("kph", "km/hr")

        match = r"(.*)\s*" + valid_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise ParseError(s, "Rate")
        d = Diff.parse(m.group(1))
        t = TV.parse(m.group(3))

        return cls(s, d, t)

    def toJSON(self) -> Any:
        return {
            "diff":     self.diff.toJSON(),
            "time":     str(self.time),
            "original": self.original
        }

    def __str__(self) -> str:
        return f"{self.diff} per {format(self.time)}"

    @classmethod
    def fromJSON(cls, jsondata: Any) -> Rate:
        diff = Diff.fromJSON(jsondata["diff"])
        time = TV(jsondata["time"])
        original = jsondata["original"]
        return cls(original, diff, time)

    @classmethod
    async def convert(cls, ctx: commands.Context[commands.Bot], argument: str) -> Rate:
        return cls.parse(argument)


class LimitedRate:
    def __init__(self, original: str, rate: Rate, stop: SV | TV):
        self.rate = rate
        self.stop = stop
        self.original = original

    @classmethod
    def parse(cls, s: str) -> LimitedRate:
        match = r"(.*)\s*" + valid_limited_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise ParseError(s, "LimitedRate")

        r = Rate.parse(m.group(1))

        st = try_or_none(SV.parse, m.group(3), (InvalidSizeValue,)) or try_or_none(TV.parse, m.group(3), (InvalidSizeValue,))

        if st is None:
            raise ParseError(s, "LimitedRate")

        return cls(s, r, st)

    def toJSON(self) -> Any:
        stoptype = "SV" if isinstance(self.stop, SV) else "TV"
        return {
            "rate": self.rate,
            "stop": self.stop,
            "original": self.original,
            "stoptype": stoptype
        }

    def __str__(self) -> str:
        joiner = "for" if isinstance(self.stop, TV) else "until"
        return f"{self.rate} {joiner} {format(self.stop)}"

    @classmethod
    def fromJSON(cls, jsondata: Any) -> LimitedRate:
        rate = Rate.fromJSON(jsondata["rate"])
        original: str = jsondata["original"]
        stoptype: str = jsondata["stoptype"]
        if stoptype == "SV":
            stop = SV(jsondata["stop"])
        elif stoptype == "TV":
            stop = TV(jsondata["stop"])
        else:
            raise ThisShouldNeverHappenException

        return cls(original, rate, stop)

    @classmethod
    async def convert(cls, ctx: commands.Context[commands.Bot], argument: str) -> LimitedRate:
        return cls.parse(argument)


def parse_change(s: str) -> LimitedRate | Rate | Diff:
    r = None
    try:
        r = LimitedRate.parse(s)
    except Exception:
        try:
            r = Rate.parse(s)
        except Exception:
            try:
                r = Diff.parse(s)
            except Exception:
                raise ParseError(s, "Diff")
    return r
