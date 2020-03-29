import random
from sizebot.lib.decimal import roundFraction


def isGood(n):
    r = roundFraction(n, 4)
    if r == 0:
        return False
    creditRating = abs(n - r) / r
    return creditRating < 0.075


def getCloseUnitsWithLimit(val, limit, units):
    return [u for u in units if 1 <= roundFraction(val / u.factor, 4) <= limit and isGood(val / u.factor)]


def getRandomCloseUnit(val, units):
    closeUnits = getCloseUnitsWithLimit(val, 6, units)
    if not closeUnits:
        closeUnits = getCloseUnitsWithLimit(val, 10, units)
    if not closeUnits:
        return None
    return random.choice(closeUnits)
