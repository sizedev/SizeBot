import traceback
import re
from itertools import zip_longest
from functools import reduce


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


# Get a value using a path in nested dicts/lists
# utils.getPath(myDict, "path.to.value", default=100)
def getPath(root, path, default=None):
    branch = root
    components = path.split(".")
    components = [tryInt(c) for c in components]
    for component in components:
        try:
            branch = branch[component]
        except (KeyError, IndexError):
            return default
    return branch


# Recurses through an attribute chain to get the ultimate value.
def deepgetattr(obj, attr):
    return reduce(lambda o, a: getattr(o, a, None), attr.split("."), obj)


# grouper(3, "ABCDEFG", "x") --> ABC DEF Gxx
def chunkStr(n, s, fillvalue=""):
    args = [iter(s)] * n
    return ("".join(chunk) for chunk in zip_longest(*args, fillvalue=fillvalue))


def removeBrackets(s):
    s = re.sub(r"[\[\]<>]", "", s)
    return s


async def sendMessage(dst, msg, maxlen=2000):
    discordPrefix = "```\n"
    discordSuffix = "\n```"
    maxlen -= len(discordPrefix) + len(discordSuffix)
    for msgPart in chunkStr(maxlen, msg):
        partToSend = discordPrefix + msgPart + discordSuffix
        await dst.send(partToSend)


def formatTraceback(err):
    return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def pformat(name, value):
    if callable(value):
        return f"{name}()"
    if isinstance(value, (list, tuple)):
        return f"{name}[]"
    if isinstance(value, set):
        return f"{name}{{}}"
    if isinstance(value, dict):
        return f"{name}{{:}}"
    return name


# return a list of an object's attributes, with type notation
def pdir(o):
    return [pformat(n, v) for n, v in ddir(o)]


# return a dictionary of an object's attributes
def ddir(o):
    return {n: getattr(o, n) for n in dir(o) if not n.startswith("_")}
