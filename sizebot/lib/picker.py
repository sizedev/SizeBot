import random

from sizebot.lib.digidecimal import round_fraction
from sizebot.lib.objs import DigiObject, objects
from sizebot.lib.units import SV


def is_good(n):
    r = round_fraction(n, 4)
    if r == 0:
        return False
    creditRating = abs(n - r) / r
    return creditRating < 0.075


def get_close_units_with_limit(val, limit, units):
    return [u for u in units if 1 <= round_fraction(val / u.factor, 4) <= limit and is_good(val / u.factor)]


def get_random_close_unit(val, units, options = 6):
    closeUnits = get_close_units_with_limit(val, options, units)
    if not closeUnits:
        closeUnits = get_close_units_with_limit(val, 10, units)
    if not closeUnits:
        return None
    return random.choice(closeUnits)


def get_close_object_smart(val: SV, tolerance: int) -> DigiObject:
    """This is a "smart" algorithm meant for use in &lookslike and &keypoints.

    Tries to get a single object for comparison, prioritizing integer closeness.
    """
    scrambled = objects.copy()
    random.shuffle(scrambled)

    sorted_list: list[tuple[float, int, DigiObject]] = []
    for n, obj in enumerate(scrambled):
        scale_ratio = obj.unitlength / val
        rounded_ratio = round_fraction(scale_ratio, tolerance)
        # random_weight prioritzes integer-ness and closeness to 1.
        random_weight = abs(1 / (rounded_ratio - scale_ratio)) - abs(rounded_ratio / 10) - 1
        sorted_list.append((random_weight, n, obj))

    sorted_list.sort()

    # Get the first ten objects and randomly select one by weight.
    possibilities = sorted_list[:10]
    return random.choices([p[2] for p in possibilities], [p[1] for p in possibilities])


def format_close_object_smart(val: SV, tolerance: int) -> str:
    obj = get_close_object_smart(val, tolerance)
    ans = round(obj.unitlength / val, 1)
    return f"{ans:.1f} {obj.name_plural if ans != 1 else obj.name}"
