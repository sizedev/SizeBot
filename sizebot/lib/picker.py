from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sizebot.lib.units import SystemUnit

import random

from sizebot.lib.digidecimal import Decimal, round_fraction


def is_good(n: Decimal) -> bool:
    r = round_fraction(n, 4)
    if r == 0:
        return False
    creditRating = abs(n - r) / r
    return creditRating < 0.075


def get_close_units_with_limit(val: Decimal, limit: Decimal, units: list[SystemUnit]) -> list[SystemUnit]:
    return [u for u in units if 1 <= round_fraction(val / u.factor, 4) <= limit and is_good(val / u.factor)]


def get_random_close_unit(val: Decimal, units: list[SystemUnit], options: Decimal = 6) -> SystemUnit:
    closeUnits = get_close_units_with_limit(val, options, units)
    if not closeUnits:
        closeUnits = get_close_units_with_limit(val, 10, units)
    if not closeUnits:
        return None
    return random.choice(closeUnits)
