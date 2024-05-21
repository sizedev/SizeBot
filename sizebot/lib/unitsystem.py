from typing import Literal, get_args

from sizebot.lib import errors
from sizebot.lib.utils import AliasMapper

UnitSystem = Literal["m", "u"]
UNITSYSTEMS = get_args(UnitSystem)

systemmap = AliasMapper[UnitSystem]({
    "m": ["b", "e", "metric", "british", "europe", "european"],
    "u": ["i", "c", "a", "us", "imperial", "customary", "american"]
})


def parse_unitsystem(s: str) -> UnitSystem:
    if s not in systemmap:
        raise errors.ArgumentException
    unitsystem = systemmap[s]
    return unitsystem
