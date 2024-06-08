from typing import Any, Hashable, Sequence
from collections.abc import Iterable

import random
import re
import traceback
from urllib.parse import quote

from discord import Embed, Message
import validator_collection

from discord.ext import commands

from sizebot.lib import errors
from sizebot.lib.types import BotContext
from sizebot.lib.units import Decimal


SECOND = 1000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
YEAR = 365 * DAY

timeunits = [
    # min    max               unit    name      frac
    (YEAR,   None,             YEAR,   "year",   False),
    (DAY,    1_000_000 * YEAR, DAY,    "day",    False),
    (HOUR,   1000 * YEAR,      HOUR,   "hour",   False),
    (MINUTE, YEAR,             MINUTE, "minute", False),
    (None,   DAY,              SECOND, "second", True)
]

def pretty_time_delta(totalSeconds: Decimal, millisecondAccuracy: bool = False, roundeventually: bool = False) -> str:
    """Get a human readable string representing an amount of time passed."""

    duration = int(totalSeconds * 1000)

    s = ""

    remaining = duration
    for mintime, maxtime, unit, name, fraction in timeunits:
        value, remaining = divmod(remaining, unit)
        if mintime is not None and duration < mintime:
                continue
        if roundeventually and maxtime is not None and duration >= maxtime:
                continue
        if millisecondAccuracy and fraction:
            s += f"{value:,d}.{remaining:03d} second{_s(value, remaining)}"
        else:
            s += f"{value:,d} {name}{_s(value)}"
    return s

def _s(value: int, fraction: int = 0) -> str:
    if value != 1 or fraction != 0:
        return "s"
    else:
        return ""


def try_int(val: Any) -> Any:
    """Try to cast `val` to an `int`, if it can't, just return `val`."""
    try:
        val = int(val)
    except ValueError:
        pass
    return val


def has_path(root: Any, path: str) -> bool:
    """Get a value using a path in nested dicts/lists."""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [try_int(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return False
    return True


def get_path(root: Any, path: str, default: Any = None) -> Any:
    """Get a value using a path in nested dicts/lists."""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [try_int(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return default
    return branch


def chunk_list(lst: list[Any], chunklen: int) -> Iterable[list[Any]]:
    while lst:
        yield lst[:chunklen]
        lst = lst[chunklen:]


def chunk_str(s: str, chunklen: int, prefix: str = "", suffix: str = "") -> Iterable[str]:
    """chunk_str(3, "ABCDEFG") --> ['ABC', 'DEF', 'G']"""
    innerlen = chunklen - len(prefix) - len(suffix)
    if innerlen <= 0:
        raise ValueError("Cannot fit prefix and suffix within chunklen")

    if not s:
        yield prefix + s + suffix
        return
    
    while len(s) > 0:
        chunk = s[:innerlen]
        s = s[innerlen:]
        yield prefix + chunk + suffix


async def sendplus(ctx: BotContext, content: str | None = None, embed: Embed | None = None, *, paged: bool = False) -> list[Message]:
    if content is not None and embed is None and paged:
        return [await ctx.send(content=c) for c in chunk_msg(content)]
    return [await ctx.send(content=content, embed=embed)] # type: ignore

def chunk_msg(m: str) -> Iterable[str]:
    p = "```\n"
    if m.startswith("Traceback") or m.startswith("eval error") or m.startswith("Executing eval"):
        p = "```python\n"
    return chunk_str(m, chunklen=2000, prefix=p, suffix="\n```")


def format_traceback(err: BaseException) -> str:
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def int_to_roman(input: int) -> str:
    """Convert an integer to a Roman numeral."""

    if not isinstance(input, type(1)):
        raise TypeError("expected integer, got %s" % type(input))
    if not 0 < input < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = []
    for i in range(len(ints)):
        count = int(input / ints[i])
        result.append(nums[i] * count)
        input -= ints[i] * count
    return ''.join(result)


async def parse_many(ctx: BotContext, arg: str, types: list[commands.Converter], default: Any = None) -> Any:
    for t in types:
        try:
            return await t.convert(ctx, arg)
        except Exception:
            pass
    return default


def is_url(value: str) -> bool:
    """Returns True when given either a valid URL, or `None`."""
    try:
        return validator_collection.url(value)
    except validator_collection.errors.EmptyValueError:
        # Pretend None is a valid URL.
        return True


def sentence_join(items: Iterable[str], *, joiner: str | None = None, oxford: bool = False) -> str:
    """Join a list of strings like a sentence.

    >>> sentence_join(['red', 'green', 'blue'])
    'red, green and blue'

    Optionally, a different joiner can be provided.

    >>> sentence_join(['micro', 'tiny', 'normal', 'amazon', 'giantess'], joiner='or')
    'micro, tiny, normal, amazon or giantess'
    """
    # Do this in case we received something like a generator, that needs to be wrapped in a list
    items = list(items)

    if len(items) == 1:
        return items[0]

    if not items:
        return ""

    if joiner is None:
        joiner = "and"

    ox = ""
    if oxford:
        ox = ","

    return f"{', '.join(items[:-1])}{ox} {joiner} {items[-1]}"


def regexbuild(li: list[str] | list[list[str]], capture: bool = False) -> str:
    """
    regexbuild(["a", "b", "c"])
    >>> "a|b|c"
    regexbuild(["a", "b", "c"], capture = True)
    >>> "(a|b|c)"
    regexbuild([["a", "b", "c"], ["x", "y", "zzz"]])
    >>> "zzz|a|b|c|x|y"
    """
    escaped: list[str] = []
    for i in li:
        if isinstance(i, list):
            for ii in i:
                escaped.append(re.escape(ii))
        else:
            escaped.append(re.escape(i))
    escaped.sort(reverse = True)
    returnstring = "|".join(escaped)
    if capture:
        returnstring = f"({returnstring})"
    return returnstring


def url_safe(s: str) -> str:
    """Makes a string URL safe, and replaces spaces with hyphens."""
    return quote(s, safe=" ").replace(" ", "-")


def truncate(s: str, amount: int) -> str:
    """Return a string that is no longer than the amount specified."""
    if len(s) > amount:
        return s[:amount - 3] + "..."
    return s


class AliasMap(dict):
    def __init__(self, data: dict[Hashable, Sequence]):
        super().__init__()

        for k, v in data.items():
            self[k] = v

    def __setitem__(self, k: Hashable, v: Sequence):
        if not isinstance(k, Hashable):
            raise ValueError("{k!r} is not hashable and can't be used as a key.")
        if not isinstance(v, Sequence):
            raise ValueError("{v!r} is not a sequence and can't be used as a value.")
        if isinstance(v, str):
            v = [v]
        for i in v:
            super().__setitem__(i, k)
        super().__setitem__(k, k)

    def __str__(self) -> str:
        swapped = {}
        for v in self.values():
            swapped[v] = []
        for k, v in self.items():
            swapped[v].append(k)

        aliasstrings = []
        for k, v in swapped.items():
            s = k
            for vv in v:
                if vv != k:
                    s += f"/{vv}"
            aliasstrings.append(s)

        return sentence_join(aliasstrings, oxford = True)


RE_SCI_EXP = re.compile(r"(\d+\.?\d*)(\*\*|\^|[Ee][\+\-]?)(\d+\.?\d*)")


def replace_sciexp(m: re.Match) -> str:
    prefix = m.group(1)
    mid = m.group(2)
    suffix = m.group(3)
    if "e" in mid.lower():
        return str(Decimal(prefix + mid + suffix))
    else:
        return str(Decimal(prefix) ** Decimal(suffix))


def replace_all_sciexp(newscale: str) -> str:
    return RE_SCI_EXP.sub(replace_sciexp, newscale)


def parse_scale(s: str) -> Decimal:
    re_scale_emoji = r"<:sb([\d\.eE]+)_?([\d\.eE]+)?:\d+>"
    if match := re.match(re_scale_emoji, s):
        if match.group(2):
            num, denom = match.group(1, 2)
            scale = Decimal(f"{num}/{denom}")
        else:
            scale = Decimal(match.group(1))
    else:
        newscale = replace_all_sciexp(s)
        re_scale = r"x?([^:/]+)[:/]?([^:/]*)?x?"
        if m := re.match(re_scale, newscale):
            multiplier = m.group(1)
            factor = m.group(2) if m.group(2) else 1
        else:
            raise errors.UserMessedUpException(f"{s} is not a valid scale factor.")

        try:
            scale = Decimal(multiplier) / Decimal(factor)
        except Exception:
            raise errors.UserMessedUpException(f"{s} is not a valid scale factor.")
    return scale


def randrange_log(minval: Decimal, maxval: Decimal, precision: int = 26) -> Decimal:
    """Generate a logarithmically scaled random number."""
    minval = Decimal(minval)
    maxval = Decimal(maxval)
    prec = Decimal(10) ** precision

    # Swap values if provided in the wrong order.
    if minval > maxval:
        minval, maxval = maxval, minval

    minlog = minval.log10()
    maxlog = maxval.log10()

    minintlog = (minlog * prec).to_integral_value()
    maxintlog = (maxlog * prec).to_integral_value()

    newintlog = Decimal(random.randint(minintlog, maxintlog))

    newlog = newintlog / prec

    newval = 10 ** newlog

    return newval


def fix_zeroes(d: Decimal) -> Decimal:
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0


def truthy(s: str) -> bool | None:
    """https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#bool"""
    lowered = s.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    return None


def join_unique(items: list[str], *, sep: str) -> str:
    return sep.join(set(items))


def round_fraction(number: Decimal, denominator: int) -> Decimal:
    """
    Round to the nearest fractional amount
    round_fraction(1.8, 4) == 1.75
    """
    rounded = round(number * denominator) / denominator
    return rounded