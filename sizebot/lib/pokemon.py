from __future__ import annotations
from typing import Any, TypedDict

import importlib.resources as pkg_resources
import json

from discord import Embed

import sizebot.data
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import User
from sizebot.lib.utils import int_to_roman

pokemon: list[Pokemon] = []


class PokemonJSON(TypedDict):
    name: str
    natdex: int
    generation: int
    region: str
    types: list[str]
    height: float
    weight: int
    color: int
    flavor_text: str
    sprite: str


class Pokemon:
    def __init__(
            self,
            name: str,
            natdex: int,
            generation: int,
            region: str,
            height: SV,
            weight: WV,
            types: list[str],
            color: int,
            flavor_text: str,
            sprite: str):
        self.name = name
        self.natdex = natdex
        self.generation = generation
        self.roman_generation = int_to_roman(self.generation)
        self.region = region
        self.height = height
        self.weight = weight
        self.types = types
        self.color = color
        self.flavor_text = flavor_text
        self.sprite = sprite

    def stats_embed(self, multiplier: Decimal = Decimal(1)) -> Embed:
        h = SV(self.height * multiplier)
        w = WV(self.weight * (multiplier ** 3))
        e = Embed()
        e.title = f"#{self.natdex} {self.name}"
        e.description = f"*from Generation {self.roman_generation} ({self.region})*\n\n{self.flavor_text}"
        e.add_field(name = "Height", value = f"{h:,.3mu}")
        e.add_field(name = "Weight", value = f"{w:,.3mu}")
        e.add_field(name = "Types", value = f"{', '.join(self.types)}")
        e.color = self.color
        e.set_image(url = self.sprite)
        e.set_footer(text = "Data from https://pokeapi.co/.")

        return e

    def comp_embed(self, user: User) -> Embed:
        h = SV(self.height * user.viewscale)
        w = WV(self.weight * (user.viewscale ** 3))
        e = Embed()
        e.title = f"#{self.natdex} {self.name} as seen by {user.nickname}"
        e.description = (f"To {user.nickname}, {self.name} looks **{h:,.3mu}** tall and weighs **{w:,.3mu}**.")
        e.color = self.color
        e.set_image(url = self.sprite)
        e.set_footer(text = f"from Generation {self.roman_generation} ({self.region}):\n{self.flavor_text}")

        return e

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            lowerName = other.lower()
            return lowerName == self.name.lower()
        elif isinstance(other, Pokemon):
            return self.name == other.name
        return False

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Pokemon):
            return self.natdex < other.natdex
        return False

    @classmethod
    def fromJSON(cls, data: PokemonJSON) -> Pokemon:
        return cls(
            data["name"],
            data["natdex"],
            data["generation"],
            data["region"],
            SV(data["height"]),
            WV(data["weight"]),
            data["types"],
            data["color"],
            data["flavor_text"],
            data["sprite"]
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


def init():
    global pokemon

    pokefile = pkg_resources.read_text(sizebot.data, "pokemon.json")
    p: list[PokemonJSON] = json.loads(pokefile)
    pokemon = [Pokemon.fromJSON(j) for j in p]
