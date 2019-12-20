import re


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


def removeBrackets(s):
    allowbrackets = ("&compare", "&stats")  # TODO: Could be better.
    if s.startswith(allowbrackets):
        return s

    s = re.sub(r"[[]<>]", "", s)

    return s
