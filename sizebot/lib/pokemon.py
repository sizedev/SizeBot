

from sizebot.lib.units import SV, WV


class Pokemon:
    def __init__(self, name, height: SV = None, weight: WV = None, types: list[str] = [], entry: str = None,
                 image: str = None, natdex: int = None) -> None:
        self.name = name
        self.height = height
        self.weight = weight
        self.types = types
        self.entry = entry
        self.image = image
        self.natdex = natdex
