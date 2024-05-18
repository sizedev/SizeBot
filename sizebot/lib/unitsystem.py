from typing import Literal, get_args

from sizebot.lib import errors

UnitSystem = Literal["m", "u"]
UNITSYSTEMS = get_args(UnitSystem)

systems = {
    "m": ("m", "b", "e", "metric", "british", "europe", "european"),
    "u": ("u", "i", "c", "a", "us", "imperial", "customary", "american")
}
systemmap = {alias: g for g, aliases in systems.items() for alias in aliases}


def parse_unitsystem(s: str) -> UnitSystem:
    unitsystem = systemmap.get(s.lower(), None)
    if unitsystem not in UNITSYSTEMS:
        raise errors.ArgumentException
    return unitsystem
