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

import re
from sizebot.lib.errors import InvalidSizeValue
from sizebot.lib.utils import regexbuild, tryOrNone
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV, TV
from typing import Literal, Union

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
    def __init__(self, original, changetype: Literal["add", "multiply", "power"], amount: Union[SV, Decimal]):
        self.changetype = changetype
        self.amount = amount
        self.original = original

    @classmethod
    def parse(cls, s):
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
                v = value

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

        return Diff(s, ct, v)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)


class Rate:
    def __init__(self, original, diff, time):
        self.diff = diff
        self.time = time
        self.original = original

    @classmethod
    def parse(cls, s):
        d = None
        t = None

        match = r"(.*)\s*" + valid_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise Exception
        d = Diff.parse(m.group(1))
        t = TV.parse(m.group(3))

        return Rate(s, d, t)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)


class LimitedRate:
    def __init__(self, original, rate, stop):
        self.rate = rate
        self.stop = stop
        self.original = original

    @classmethod
    def parse(cls, s):
        r = None
        st = None

        match = r"(.*)\s*" + valid_limited_rate_interfixes + r"\s*(.*)"
        m = re.match(match, s)
        if not m:
            raise Exception

        r = Rate.parse(m.group(1))

        st = tryOrNone(SV.parse, m.group(3), (InvalidSizeValue,)) or tryOrNone(TV.parse, m.group(3), (InvalidSizeValue,))

        if st is None:
            raise Exception

        return LimitedRate(s, r, st)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)


def parse_change(s):
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
                Exception
    return r


print("hi")
