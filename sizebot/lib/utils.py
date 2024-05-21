from typing import Any
from collections.abc import Iterable

import random
import re
import traceback
from urllib.parse import quote

import validator_collection
import validator_collection.errors

from sizebot.lib.digidecimal import Decimal
from sizebot.lib import errors

re_num = r"\d+\.?\d*"


def pretty_time_delta(totalSeconds: Decimal, millisecondAccuracy: bool = False, roundeventually: bool = False) -> str:
    """Get a human readable string representing an amount of time passed."""
    MILLISECONDS_PER_YEAR = 86400 * 365 * 1000
    MILLISECONDS_PER_DAY = 86400 * 1000
    MILLISECONDS_PER_HOUR = 3600 * 1000
    MILLISECONDS_PER_MINUTE = 60 * 1000
    MILLISECONDS_PER_SECOND = 1000

    inputms = milliseconds = int(totalSeconds * 1000)
    years, milliseconds = divmod(milliseconds, MILLISECONDS_PER_YEAR)
    days, milliseconds = divmod(milliseconds, MILLISECONDS_PER_DAY)
    hours, milliseconds = divmod(milliseconds, MILLISECONDS_PER_HOUR)
    minutes, milliseconds = divmod(milliseconds, MILLISECONDS_PER_MINUTE)
    seconds, milliseconds = divmod(milliseconds, MILLISECONDS_PER_SECOND)

    s = ""
    if not roundeventually or inputms <= MILLISECONDS_PER_DAY:
        if inputms >= MILLISECONDS_PER_YEAR:
            s += f"{years:,d} year{'s' if years != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_DAY:
            s += f"{days:,d} day{'s' if days != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_HOUR:
            s += f"{hours:,d} hour{'s' if hours != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_MINUTE:
            s += f"{minutes:,d} minute{'s' if minutes != 1 else ''}, "
        if millisecondAccuracy:
            s += f"{seconds:,d}.{milliseconds:03d} second{'' if seconds == 1 and milliseconds == 0 else 's'}"
        else:
            s += f"{seconds:,d} second{'s' if seconds != 1 else ''}"
    elif inputms >= MILLISECONDS_PER_YEAR * 1_000_000:
        if inputms >= MILLISECONDS_PER_YEAR:
            s += f"{years:,d} year{'s' if years != 1 else ''}"
    elif inputms >= MILLISECONDS_PER_YEAR * 1000:
        if inputms >= MILLISECONDS_PER_YEAR:
            s += f"{years:,d} year{'s' if years != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_DAY:
            s += f"{days:,d} day{'s' if days != 1 else ''}"
    elif inputms >= MILLISECONDS_PER_YEAR:
        if inputms >= MILLISECONDS_PER_YEAR:
            s += f"{years:,d} year{'s' if years != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_DAY:
            s += f"{days:,d} day{'s' if days != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_HOUR:
            s += f"{hours:,d} hour{'s' if hours != 1 else ''}"
    elif inputms >= MILLISECONDS_PER_DAY:
        if inputms >= MILLISECONDS_PER_YEAR:
            s += f"{years:,d} year{'s' if years != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_DAY:
            s += f"{days:,d} day{'s' if days != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_HOUR:
            s += f"{hours:,d} hour{'s' if hours != 1 else ''}, "
        if inputms >= MILLISECONDS_PER_MINUTE:
            s += f"{minutes:,d} minute{'s' if minutes != 1 else ''}"

    return s


def try_int(val: Any) -> Any:
    """Try to cast `val` to an `int`, if it can't, just return `val`."""
    try:
        val = int(val)
    except ValueError:
        pass
    return val


def chunk_list[T](lst: list[T], chunklen: int) -> Iterable[list[T]]:
    while lst:
        yield lst[:chunklen]
        lst = lst[chunklen:]


def _chunk_str(s: str, chunklen: int, prefix: str = "", suffix: str = "") -> Iterable[str]:
    """chunk_str(3, "ABCDEFG") --> ['ABC', 'DEF', 'G']"""
    innerlen = chunklen - len(prefix) - len(suffix)
    if innerlen <= 0:
        raise ValueError("Cannot fit prefix and suffix within chunklen")

    while len(s) > 0:
        chunk = s[:innerlen]
        s = s[innerlen:]
        yield prefix + chunk + suffix


def chunk_msg(m: str) -> list[str]:
    p = "```\n"
    if m.startswith("Traceback") or m.startswith("eval error") or m.startswith("Executing eval"):
        p = "```python\n"
    return list(_chunk_str(m, chunklen=2000, prefix=p, suffix="\n```"))


def format_traceback(err: BaseException) -> str:
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def get_fullname(o: object) -> str:
    moduleName = o.__class__.__module__
    if moduleName == "builtins":
        moduleName = ""
    if moduleName:
        moduleName = f"{moduleName}."

    className = o.__class__.__name__
    fullname = f"{moduleName}{className}"
    return fullname


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


def is_url(value: str) -> bool:
    """Returns True when given either a valid URL, or `None`."""
    try:
        return validator_collection.url(value)
    except validator_collection.errors.EmptyValueError:
        # Pretend None is a valid URL.
        return True


def url_safe(s: str) -> str:
    """Makes a string URL safe, and replaces spaces with hyphens."""
    return quote(s, safe=" ").replace(" ", "-")


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


def truncate(s: str, amount: int) -> str:
    """Return a string that is no longer than the amount specified."""
    if len(s) > amount:
        return s[:amount - 3] + "..."
    return s


RE_SCI_EXP = re.compile(r"(\d+\.?\d*)(\*\*|\^|[Ee][\+\-]?)(\d+\.?\d*)")


def _replace_sciexp(m: re.Match) -> str:
    prefix = m.group(1)
    mid = m.group(2)
    suffix = m.group(3)
    if "e" in mid.lower():
        return str(Decimal(prefix + mid + suffix))
    else:
        return str(Decimal(prefix) ** Decimal(suffix))


def _replace_all_sciexp(newscale: str) -> str:
    return RE_SCI_EXP.sub(_replace_sciexp, newscale)


def parse_scale(s: str) -> Decimal:
    re_scale_emoji = r"<:sb([\d\.eE]+)_?([\d\.eE]+)?:\d+>"
    if match := re.match(re_scale_emoji, s):
        if match.group(2):
            num, denom = match.group(1, 2)
            scale = Decimal(f"{num}/{denom}")
        else:
            scale = Decimal(match.group(1))
    else:
        newscale = _replace_all_sciexp(s)
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


def round_fraction(number: Decimal, denominator: int) -> Decimal:
    rounded = round(number * denominator) / denominator
    return rounded
