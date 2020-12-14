from copy import copy
from PIL import Image

from sizebot.lib.diff import Diff
from sizeroyale.lib.errors import ParseError
from sizebot.lib.units import SV
from sizebot.lib.utils import isURL
from sizeroyale.lib.classes.metaparser import MetaParser
from sizeroyale.lib.errors import GametimeError, ThisShouldNeverHappenException
from sizeroyale.lib.img_utils import create_profile_picture


class Player:
    valid_data = [("team", "single"), ("gender", "single"), ("height", "single"), ("url", "single"), ("attr", "list"), ("nsfw", "single")]

    def __init__(self, game, name: str, meta: str):
        self._game = game
        self._original_metadata = meta
        self._metadata = MetaParser(type(self)).parse(meta)
        self.name = name
        self.team = self._metadata.team
        self.gender = self._metadata.gender
        self.height = SV.parse(self._metadata.height) if isinstance(self._metadata.height, str) else SV.parse(str(self._metadata.height) + "m")
        self.baseheight = copy(self.height)
        if not isURL(self._metadata.url):
            raise ValueError(f"{self._metadata.url} is not a URL.")
        self.url = self._metadata.url
        self.attributes = [] if self._metadata.attr is None else self._metadata.attr
        if self._metadata.nsfw is None or self._metadata.nsfw.lower() == "true":
            self.nsfw = True
        elif self._metadata.nsfw.lower() == "false":
            self.nsfw = False
        else:
            raise ParseError(f"{self._metadata.nsfw!r} is not a valid NSFW flag.")

        self.inventory = []
        self.dead = False
        self.elims = 0

    async def get_image(self) -> Image:
        return await create_profile_picture(self._game.royale.unitsystem, self.url, self.name, self.team, self.height, self.dead)

    @property
    def subject(self) -> str:
        if self.gender == "M":
            return "he"
        elif self.gender == "F":
            return "she"
        elif self.gender == "X":
            return "they"

    @property
    def object(self) -> str:
        if self.gender == "M":
            return "him"
        elif self.gender == "F":
            return "her"
        elif self.gender == "X":
            return "them"
        else:
            raise ThisShouldNeverHappenException(f"Invalid gender {self.gender!r} on player {self.name!r}.")

    @property
    def posessive(self) -> str:
        if self.gender == "M":
            return "his"
        elif self.gender == "F":
            return "her"
        elif self.gender == "X":
            return "their"
        else:
            raise ThisShouldNeverHappenException(f"Invalid gender {self.gender!r} on player {self.name!r}.")

    # Unused, hope we don't need this.
    @property
    def posessive2(self) -> str:
        if self.gender == "M":
            return "his"
        elif self.gender == "F":
            return "hers"
        elif self.gender == "X":
            return "theirs"
        else:
            raise ThisShouldNeverHappenException(f"Invalid gender {self.gender!r} on player {self.name!r}.")

    @property
    def reflexive(self) -> str:
        if self.gender == "M":
            return "himself"
        elif self.gender == "F":
            return "herself"
        elif self.gender == "X":
            return "themself"
        else:
            raise ThisShouldNeverHappenException(f"Invalid gender {self.gender!r} on player {self.name!r}.")

    def give_item(self, item: str):
        self.inventory.append(item)

    def remove_item(self, item: str):
        if item in self.inventory:
            self.inventory.remove(item)
        else:
            raise GametimeError(f"{self.name} has no item {self.item!r}!")

    def clear_inventory(self):
        self.inventory = []

    def give_attribute(self, attribute: str):
        self.inventory.append(attribute)

    def remove_attribute(self, attribute: str):
        if attribute in self.inventory:
            self.inventory.remove(attribute)
        else:
            raise GametimeError(f"{self.name} has no attribute {self.attribute!r}!")

    def change_height(self, diff: Diff):
        if diff.changetype == "add":
            self.height = SV(self.height + diff.amount)
        elif diff.changetype == "multiply":
            self.height = SV(self.height * diff.amount)

        else:
            raise GametimeError(f"Unsupported changetype {diff.changetype!r}.")

    def __lt__(self, other):
        if self.team != other.team:
            return int(self.team) < int(other.team)
        return self.name < other.name

    def __str__(self):
        return f"**{self.name}**: Team {self.team}, Gender {self.gender}, Height {self.height}, Eliminations: {self.elims}, Inventory: {'Empty' if self.inventory == [] else self.inventory}. *{'Dead.' if self.dead else 'Alive.'}*"

    def __repr__(self):
        return f"Player(name={self.name!r}, team={self.team!r}, gender={self.gender!r}, height={self.height!r}, url={self.url!r}, inventory={self.inventory!r})"
