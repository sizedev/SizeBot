from typing import Literal, get_args

from sizebot.lib import errors

UnitSystem = Literal["m", "u"]
UNITSYSTEMS = get_args(UnitSystem)

systems: dict[UnitSystem, list[str]] = {
    "m": ["m", "b", "e", "metric", "british", "europe", "european"],
    "u": ["u", "i", "c", "a", "us", "imperial", "customary", "american"]
}
systemmap: dict[str, UnitSystem] = {alias: key for key, aliases in systems.items() for alias in aliases}


def parse_unitsystem(s: str) -> UnitSystem:
    unitsystem = systemmap.get(s.lower(), None)
    if unitsystem is None or unitsystem not in UNITSYSTEMS:
        raise errors.ArgumentException
    return unitsystem
