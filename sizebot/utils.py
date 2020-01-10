import pydoc
import inspect
import traceback
import re
from functools import reduce

re_num = "\\d+\\.?\\d*"


def clamp(minVal, val, maxVal):
    return max(minVal, min(maxVal, val))


def prettyTimeDelta(totalSeconds):
    SECONDS_PER_YEAR = 86400 * 365
    SECONDS_PER_DAY = 86400
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60

    seconds = int(totalSeconds)
    years, seconds = divmod(seconds, SECONDS_PER_YEAR)
    days, seconds = divmod(seconds, SECONDS_PER_DAY)
    hours, seconds = divmod(seconds, SECONDS_PER_HOUR)
    minutes, seconds = divmod(seconds, SECONDS_PER_MINUTE)

    s = ""
    if totalSeconds >= SECONDS_PER_YEAR:
        s += f"{years:d} years, "
    if totalSeconds >= SECONDS_PER_DAY:
        s += f"{days:d} days, "
    if totalSeconds >= SECONDS_PER_HOUR:
        s += f"{hours:d} hours, "
    if totalSeconds >= SECONDS_PER_MINUTE:
        s += f"{minutes:d} minutes, "
    s += f"{seconds:d} seconds"


def tryInt(val):
    try:
        val = int(val)
    except ValueError:
        pass
    return val


def getPath(root, path, default=None):
    """Get a value using a path in nested dicts/lists"""
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


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(lambda o, a: getattr(o, a, None), attr.split("."), obj)


def chunkStr(s, n):
    """chunkStr(3, "ABCDEFG") --> ['ABC', 'DEF', 'G']"""
    if s == 0:
        return [""]
    while len(s) > 0:
        chunk = s[:n]
        s = s[n:]
        yield chunk


def chunkMsg(m, *, maxlen=2000, prefix="```\n", suffix="\n```"):
    for chunk in chunkStr(m, maxlen - len(prefix) - len(suffix)):
        yield prefix + chunk + suffix


def removeBrackets(s):
    s = re.sub(r"[\[\]<>]", "", s)
    return s


def formatTraceback(err):
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def pformat(name, value):
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
    """return a list of an object's attributes, with type notation"""
    return [pformat(n, v) for n, v in ddir(o).items()]


def ddir(o):
    """return a dictionary of an object's attributes"""
    return {n: v for n, v in inspect.getmembers(o) if not n.startswith("_")}
    # return {n: getattr(o, n, None) for n in dir(o) if not n.startswith("_")}


def formatError(err):

    moduleName = err.__class__.__module__
    if moduleName == "builtins":
        moduleName = ""
    if moduleName:
        moduleName = f"{moduleName}."

    className = err.__class__.__name__

    errMessage = str(err)
    if errMessage:
        errMessage = f": {errMessage}"

    return f"{moduleName}{className}{errMessage}"


formatSpecRe = re.compile(r"""\A
(?:
   (?P<fill>.)?
   (?P<align>[<>=^])
)?
(?P<sign>[-+ ])?
(?P<zeropad>0)?
(?P<minimumwidth>(?!0)\d+)?
(?P<thousands_sep>,)?
(?:\.(?P<precision>0|(?!0)\d+))?
(?P<type>[a-zA-Z]{1,2})?
(?P<fractional>%)?
\Z
""", re.VERBOSE)


def parseSpec(spec):
    m = formatSpecRe.match(spec)
    if m is None:
        raise ValueError("Invalid format specifier: " + spec)
    return m.groupdict()


def buildSpec(formatDict):
    spec = ""
    if formatDict["align"] is not None:
        if formatDict["fill"] is not None:
            spec += formatDict["fill"]
        spec += formatDict["align"]
    if formatDict["sign"] is not None:
        spec += formatDict["sign"]
    if formatDict["zeropad"] is not None:
        spec += formatDict["zeropad"]
    if formatDict["minimumwidth"] is not None:
        spec += formatDict["minimumwidth"]
    if formatDict["thousands_sep"] is not None:
        spec += formatDict["thousands_sep"]
    if formatDict["precision"] is not None:
        spec += "." + formatDict["precision"]
    if formatDict["type"] is not None:
        spec += formatDict["type"]
    return spec


def tryOrNone(fn, *args, ignore=(), **kwargs):
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


def strHelp(topic):
    return pydoc.plain(pydoc.render_doc(topic))


def minmax(first, second):
    small, big = first, second
    if small > big:
        small, big = big, small
    return small, big
