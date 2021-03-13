import inspect
import pydoc
import random
import re
import traceback
from typing import Dict, Hashable, Sequence
from urllib.parse import quote

import validator_collection

from sizebot.lib.digidecimal import Decimal

re_num = r"\d+\.?\d*"

glitch_template = ("V2UncmUgbm8gc3RyYW5nZXJzIHRvIGxvdmUgLyBZb3Uga25vdyB0aGUgcnVsZXMgYW5kIHNvIGRv"
                   "IEkgLyBBIGZ1bGwgY29tbWl0bWVudCdzIHdoYXQgSSdtIHRoaW5raW5nIG9mIC9Zb3Ugd291bGRu"
                   "J3QgZ2V0IHRoaXMgZnJvbSBhbnkgb3RoZXIgZ3V5IC8gSSBqdXN0IHdhbm5hIHRlbGwgeW91IGhv"
                   "dyBJJ20gZmVlbGluZyAvIEdvdHRhIG1ha2UgeW91IHVuZGVyc3RhbmQgLyBOZXZlciBnb25uYSBn"
                   "aXZlIHlvdSB1cCAvIE5ldmVyIGdvbm5hIGxldCB5b3UgZG93biAvIE5ldmVyIGdvbm5hIHJ1biBh"
                   "cm91bmQgYW5kIGRlc2VydCB5b3UgLyBOZXZlciBnb25uYSBtYWtlIHlvdSBjcnkgLyBOZXZlciBn"
                   "b25uYSBzYXkgZ29vZGJ5ZSAvIE5ldmVyIGdvbm5hIHRlbGwgYSBsaWUgYW5kIGh1cnQgeW91")

current_glitch_index = 0


def clamp(minVal, val, maxVal):
    """Clamp a `val` to be no lower than `minVal`, and no higher than `maxVal`."""
    return max(minVal, min(maxVal, val))


def prettyTimeDelta(totalSeconds, millisecondAccuracy = False, roundeventually = False) -> str:
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


def tryInt(val):
    """Try to cast `val` to an `int`, if it can't, just return `val`."""
    try:
        val = int(val)
    except ValueError:
        pass
    return val


def hasPath(root, path):
    """Get a value using a path in nested dicts/lists."""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [tryInt(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return False
    return True


def getPath(root, path, default=None):
    """Get a value using a path in nested dicts/lists."""
    """utils.getPath(myDict, "path.to.value", default=100)"""
    branch = root
    components = path.split(".")
    components = [tryInt(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return default
    return branch


def chunkList(lst, chunklen):
    while lst:
        yield lst[:chunklen]
        lst = lst[chunklen:]


def chunkStr(s, chunklen, prefix="", suffix=""):
    """chunkStr(3, "ABCDEFG") --> ['ABC', 'DEF', 'G']"""
    innerlen = chunklen - len(prefix) - len(suffix)
    if innerlen <= 0:
        raise ValueError("Cannot fit prefix and suffix within chunklen")

    if not s:
        return prefix + s + suffix

    while len(s) > 0:
        chunk = s[:innerlen]
        s = s[innerlen:]
        yield prefix + chunk + suffix


def chunkMsg(m) -> list:
    p = "```\n"
    if m.startswith("Traceback") or m.startswith("eval error") or m.startswith("Executing eval"):
        p = "```python\n"
    return chunkStr(m, chunklen=2000, prefix=p, suffix="\n```")


def chunkLines(s, chunklen):
    """Split a string into groups of lines that don't go over the chunklen. Individual lines longer the chunklen will be split"""
    lines = s.split("\n")

    linesout = []
    while lines:
        linesout.append(lines.pop(0))
        if len("\n".join(linesout)) > chunklen:
            if len(linesout) == 1:
                line = linesout.pop()
                lines.insert(0, line[chunklen:])
                linesout.append(line[:chunklen])
            else:
                lines.insert(0, linesout.pop())
            yield "\n".join(linesout)
            linesout = []
    if linesout:
        yield "\n".join(linesout)


def removeBrackets(s) -> str:
    """Remove all [] and <>s from a string."""
    s = re.sub(r"[\[\]<>]", "", s)
    return s


def formatTraceback(err) -> str:
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def pformat(name, value) -> str:
    if value is None:
        return f"{name}?"
    if callable(value):
        return f"{name}()"
    if isinstance(value, (list, tuple)):
        return f"{name}[]"
    if isinstance(value, set):
        return f"{name}{{}}"
    if isinstance(value, dict):
        return f"{name}{{:}}"
    return name


def pdir(o):
    """return a list of an object's attributes, with type notation."""
    return [pformat(n, v) for n, v in ddir(o).items()]


def ddir(o):
    """return a dictionary of an object's attributes."""
    return {n: v for n, v in inspect.getmembers(o) if not n.startswith("_")}
    # return {n: getattr(o, n, None) for n in dir(o) if not n.startswith("_")}


def getFullname(o):
    moduleName = o.__class__.__module__
    if moduleName == "builtins":
        moduleName = ""
    if moduleName:
        moduleName = f"{moduleName}."

    className = o.__class__.__name__
    fullname = f"{moduleName}{className}"
    return fullname


def formatError(err) -> str:
    fullname = getFullname(err)

    errMessage = str(err)
    if errMessage:
        errMessage = f": {errMessage}"

    return f"{fullname}{errMessage}"


def tryOrNone(fn, *args, ignore=(), **kwargs):
    "Try to run a function. If it throws an error that's in `ignore`, just return `None`."""
    try:
        result = fn(*args, **kwargs)
    except ignore:
        result = None
    return result


class iset(set):
    def __init__(self, iterable):
        iterable = (i.casefold() for i in iterable)
        super().__init__(iterable)

    def add(self, item):
        item = item.casefold()
        return super().add(item)

    def __contains__(self, item):
        item = item.casefold()
        return super().__contains__(item)

    def discard(self, item):
        item = item.casefold()
        return super().discard(item)

    def remove(self, item):
        item = item.casefold()
        return super().remove(item)


def strHelp(topic) -> str:
    return pydoc.plain(pydoc.render_doc(topic))


def minmax(first, second) -> tuple:
    """Return a tuple where item 0 is the smaller value, and item 1 is the larger value."""
    small, big = first, second
    if small > big:
        small, big = big, small
    return small, big


def removeCodeBlock(s) -> str:
    re_codeblock = re.compile(r"^\s*```(?:python)?(.*)```\s*$", re.DOTALL)
    s_nocodeblock = re.sub(re_codeblock, r"\1", s)
    if s_nocodeblock != s:
        return s_nocodeblock

    re_miniblock = re.compile(r"^\s*`(.*)`\s*$", re.DOTALL)
    s_nominiblock = re.sub(re_miniblock, r"\1", s)
    if s_nominiblock != s:
        return s_nominiblock

    return s


def intToRoman(input) -> str:
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


def findOne(iterator):
    try:
        val = next(iterator)
    except StopIteration:
        val = None
    return val


async def parseMany(ctx, arg, types: list, default = None):
    for t in types:
        try:
            return await t.convert(ctx, arg)
        except Exception:
            pass
    return default


def isURL(value) -> bool:
    """Returns True when given either a valid URL, or `None`."""
    try:
        return validator_collection.url(value)
    except validator_collection.errors.EmptyValueError:
        # Pretend None is a valid URL.
        return True


def sentence_join(items, *, joiner=None, oxford=False) -> str:
    """Join a list of strings like a sentence.

    >>> sentence_join(['red', 'green', 'blue'])
    'red, green and blue'

    Optionally, a different joiner can be provided.

    >>> sentence_join(['micro', 'tiny', 'normal', 'amazon', 'giantess'], joiner='or')
    'micro, tiny, normal, amazon or giantess'
    """
    if not items:
        return ""

    if joiner is None:
        joiner = "and"

    ox = ""
    if oxford:
        ox = ","

    # Do this in case we received something like a generator, that needs to be wrapped in a list
    items = list(items)

    if len(items) == 1:
        return items[0]

    return f"{', '.join(items[:-1])}{ox} {joiner} {items[-1]}"


# TODO: Deprecated, use Python 3.9's methods
def removeprefix(self: str, prefix: str, /) -> str:
    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self[:]


# TODO: Deprecated, use Python 3.9's methods
def removesuffix(self: str, suffix: str, /) -> str:
    # suffix='' should not call self[:-0].
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]


def glitch_string(in_string: str, *, charset = None) -> str:
    words = []
    if charset is not None:
        for word in in_string.split(" "):
            words.append(''.join(random.choices(charset, k=len(word))))
    else:
        global current_glitch_index
        for word in in_string.split(" "):
            k = len(word)
            new_word = glitch_template[current_glitch_index:current_glitch_index + k]
            k -= len(new_word)
            if k != 0:
                current_glitch_index = 0
                new_word = glitch_template[current_glitch_index:current_glitch_index + k]
            words.append(new_word)
            current_glitch_index += len(new_word)
    return " ".join(words)


def regexbuild(li: list, capture = False) -> str:
    """
    regexbuild(["a", "b", "c"])
    >>> "a|b|c"
    regexbuild(["a", "b", "c"], capture = True)
    >>> "(a|b|c)"
    regexbuild([["a", "b", "c"], ["x", "y", "zzz"]])
    >>> "zzz|a|b|c|x|y"
    """
    escaped = []
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


def url_safe(s) -> str:
    """Makes a string URL safe, and replaces spaces with hyphens."""
    return quote(s, safe=" ").replace(" ", "-")


def truncate(s, amount) -> str:
    """Return a string that is no longer than the amount specified."""
    if len(s) > amount:
        return s[:amount - 3] + "..."
    return s


class AliasMap(dict):
    def __init__(self, data: Dict[Hashable, Sequence]):
        super().__init__()

        for k, v in data.items():
            self[k] = v

    def __setitem__(self, k, v):
        if not isinstance(k, Hashable):
            raise ValueError("{k!r} is not hashable and can't be used as a key.")
        if not isinstance(v, Sequence):
            raise ValueError("{v!r} is not a sequence and can't be used as a value.")
        if isinstance(v, str):
            v = [v]
        for i in v:
            super().__setitem__(i, k)
        super().__setitem__(k, k)

    def __str__(self):
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


def undo_powers(matchobj: re.Match):
    prefix = matchobj.group(1)
    mid = matchobj.group(2)
    suffix = matchobj.group(3)

    if "e" in mid.lower():
        return str(Decimal(prefix + mid + suffix))
    else:
        return str(Decimal(prefix) ** Decimal(suffix))


def randRangeLog(minval, maxval, precision=26):
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


def roundFraction(number, denominator):
    rounded = round(number * denominator) / denominator
    return rounded


def fixZeroes(d):
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0
