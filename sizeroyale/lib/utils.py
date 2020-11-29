import inspect
import re
import traceback

import validator_collection


def clamp(minVal, val, maxVal):
    """Clamp a `val` to be no lower than `minVal`, and no higher than `maxVal`."""
    return max(minVal, min(maxVal, val))


def prettyTimeDelta(totalSeconds, millisecondAccuracy = False) -> str:
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
    if inputms >= MILLISECONDS_PER_YEAR:
        s += f"{years:d} years, "
    if inputms >= MILLISECONDS_PER_DAY:
        s += f"{days:d} days, "
    if inputms >= MILLISECONDS_PER_HOUR:
        s += f"{hours:d} hours, "
    if inputms >= MILLISECONDS_PER_MINUTE:
        s += f"{minutes:d} minutes, "
    if millisecondAccuracy:
        s += f"{seconds:d}.{milliseconds:03d} seconds"
    else:
        s += f"{seconds:d} seconds"

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


def minmax(first, second) -> tuple:
    """Return a tuple where item 0 is the smaller value, and item 1 is the larger value."""
    small, big = first, second
    if small > big:
        small, big = big, small
    return small, big


def findOne(iterator):
    try:
        val = next(iterator)
    except StopIteration:
        val = None
    return val


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


def truncate(s, amount) -> str:
    """Return a string that is no longer than the amount specified."""
    if len(s) > amount:
        return s[:amount - 3] + "..."
    return s


def hasattr(obj, key):
    try:
        obj.__getattr__(key)
        return True
    except AttributeError:
        return False
