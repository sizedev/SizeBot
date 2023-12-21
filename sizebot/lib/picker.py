import random

from sizebot.lib.digidecimal import round_fraction


def is_good(n):
    r = round_fraction(n, 4)
    if r == 0:
        return False
    creditRating = abs(n - r) / r
    return creditRating < 0.075


def get_close_units_with_limit(val, limit, units):
    return [u for u in units if 1 <= round_fraction(val / u.factor, 4) <= limit and is_good(val / u.factor)]


def get_random_close_unit(val, units):
    closeUnits = get_close_units_with_limit(val, 6, units)
    if not closeUnits:
        closeUnits = get_close_units_with_limit(val, 10, units)
    if not closeUnits:
        return None
    return random.choice(closeUnits)
