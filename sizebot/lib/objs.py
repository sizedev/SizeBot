from __future__ import annotations
from typing import Literal, Any, NotRequired, TypedDict, cast

from functools import total_ordering
import importlib.resources as pkg_resources
import json
import math
import random

from discord import Embed

import sizebot.data.objects
from sizebot import __version__
from sizebot.lib import errors, userdb
from sizebot.lib.language import get_plural, get_indefinite_article
from sizebot.lib.types import BotContext
from sizebot.lib.units import AV, SV, VV, WV, Unit, SystemUnit, Decimal
from sizebot.lib.utils import sentence_join

objects: list[DigiObject] = []
food: list[DigiObject] = []
land: list[DigiObject] = []
tags: dict[str, int] = {}

Dimension = Literal["h", "l", "d", "w", "t", "p"]


class ObjectJson(TypedDict):
    name: str
    dimension: Dimension
    aliases: NotRequired[list[str]]
    tags: NotRequired[list[str]]
    symbol: NotRequired[str]
    height: NotRequired[str]    # SV
    length: NotRequired[str]    # SV
    width: NotRequired[str]     # SV
    diameter: NotRequired[str]  # SV
    depth: NotRequired[str]     # SV
    thickness: NotRequired[str] # SV
    calories: NotRequired[str]  # Decimal
    price: NotRequired[str]     # Decimal
    weight: NotRequired[str]    # WV
    note: NotRequired[str]


class LandJson(TypedDict):
    name: str
    dimension: Dimension
    aliases: NotRequired[list[str]]
    tags: NotRequired[list[str]]
    height: str    # SV
    length: str    # SV
    width: str     # SV
    note: NotRequired[str]


@total_ordering
class DigiObject:
    def __init__(
        self,
        name: str,
        dimension: Dimension,
        aliases: list[str],
        tags: list[str],
        symbol: str | None,
        height: SV | None,
        length: SV | None,
        width: SV | None,
        diameter: SV | None,
        depth: SV | None,
        thickness: SV | None,
        calories: Decimal | None,
        price: Decimal | None,
        weight: WV | None,
        note: str | None
    ):
        self.name = name
        self.dimension: Dimension = dimension
        self.name_plural = get_plural(name)
        self.singular_names = aliases + [self.name]
        self.aliases = aliases + [get_plural(a) for a in aliases]
        self.aliases = self.aliases + [a.replace("™", "").replace("®", "") for a in self.aliases + [self.name]]  # Remove ®, ™
        self.aliases = list(set(self.aliases))  # Remove duplicates
        self._tags = tags
        self.tags = tags + [get_plural(t) for t in self._tags]
        self.article = get_indefinite_article(self.name).split(" ")[0]
        self.symbol = symbol
        self.note = note

        self.height = height
        self.length = length
        self.width = width
        self.diameter = diameter
        self.depth = depth
        self.thickness = thickness
        self.calories = calories
        self.price = price
        self.weight = weight

    @property
    def unitlength(self) -> SV:
        dimensionmap = {
            "h": self.height,
            "l": self.length,
            "w": self.width,
            "d": self.diameter,
            "p": self.depth,
            "t": self.thickness,
        }
        return cast(SV, dimensionmap[self.dimension])

    @property
    def area(self) -> AV | None:
        if self.height is not None and self.width is not None:
            return self.height * self.width
        elif self.length is not None and self.width is not None:
            return self.length * self.width
        elif self.diameter:
            r = self.diameter / 2
            r2 = r ** 2
            return Decimal(math.pi) * r2
        return None

    @property
    def volume(self) -> VV | None:
        if self.area is not None:
            if self.depth is not None:
                return self.area * self.depth
            elif self.thickness is not None:
                return self.area * self.thickness
        return None

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            lowerName = other.lower()
            return lowerName == self.name.lower() \
                or lowerName == self.name_plural \
                or lowerName in (n.lower() for n in self.aliases)
        elif isinstance(other, DigiObject):
            return (self.name, self.unitlength) == (other.name, other.unitlength)
        return super().__eq__(other)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, DigiObject):
            return self.unitlength < other.unitlength
        return self.unitlength < other

    @classmethod
    def find_by_name(cls, name: str) -> DigiObject | None:
        lowerName = name.lower()
        for o in objects:
            if o == lowerName:
                return o
        lowerName = lowerName.removeprefix("random").strip()
        tagged = [o for o in objects if lowerName in o.tags]
        if tagged:
            return random.choice(tagged)
        return None

    @classmethod
    def from_json(cls, data: ObjectJson) -> DigiObject:
        name = data["name"]
        dimension = data["dimension"]
        aliases = data.get("aliases", [])
        tags = data.get("tags", [])
        symbol = data.get("symbol")
        height = SV(data["height"]) if "height" in data else None
        length = SV(data["length"]) if "length" in data else None
        width = SV(data["width"]) if "width" in data else None
        diameter = SV(data["diameter"]) if "diameter" in data else None
        depth = SV(data["depth"]) if "depth" in data else None
        thickness = SV(data["thickness"]) if "thickness" in data else None
        calories = Decimal(data["calories"]) if "calories" in data else None
        price = Decimal(data["price"]) if "price" in data else None
        weight = WV(data["weight"]) if "weight" in data else None
        note = data.get("note")
        return cls(name, dimension, aliases, tags, symbol, height, length, width, diameter, depth, thickness, calories, price, weight, note)

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> DigiObject:
        obj = cls.find_by_name(argument)
        if obj is None:
            raise errors.InvalidObject(argument)
        return obj

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class DigiLand:
    def __init__(
        self,
        name: str,
        dimension: Dimension,
        height: SV,
        length: SV,
        width: SV,
        tags: list[str],
        note: str | None
    ):
        self.name = name
        self.dimension = dimension
        self.height = height
        self.length = length
        self.width = width
        self.tags = tags
        self.note = note

    @property
    def area(self) -> AV:
        return self.height * self.width

    @classmethod
    def from_digiobject(cls, obj: DigiObject) -> DigiLand:
        return cls(
            name=obj.name,
            dimension=obj.dimension,
            height=cast(SV, obj.height),
            length=cast(SV, obj.length),
            width=cast(SV, obj.width),
            tags=obj.tags,
            note=obj.note
        )




def _get_stats_embed(obj: DigiObject, multiplier: Decimal = Decimal(1)) -> Embed:
    embed = Embed()
    embed.set_author(name = f"SizeBot {__version__}")

    if obj.height:
        embed.add_field(name = "Height",
                        value = f"**{SV(obj.height * multiplier):,.3mu}** tall\n")
    if obj.length:
        embed.add_field(name = "Length",
                        value = f"**{SV(obj.length * multiplier):,.3mu}** long\n")
    if obj.width:
        embed.add_field(name = "Width",
                        value = f"**{SV(obj.width * multiplier):,.3mu}** wide\n")
    if obj.diameter:
        embed.add_field(name = "Diameter",
                        value = f"**{SV(obj.diameter * multiplier):,.3mu}** across\n")
    if obj.depth:
        embed.add_field(name = "Depth",
                        value = f"**{SV(obj.depth * multiplier):,.3mu}** deep\n")
    if obj.thickness:
        embed.add_field(name = "Thickness",
                        value = f"**{SV(obj.thickness * multiplier):,.3mu}** thick\n")
    if obj.area is not None:
        embed.add_field(name = "Area",
                        value = f"**{AV(obj.area * (multiplier ** 2)):,.3mu}**\n")
    if obj.volume is not None:
        embed.add_field(name = "Volume",
                        value = f"**{VV(obj.volume * (multiplier ** 3)):,.3mu}**\n")
    if obj.calories is not None:
        embed.add_field(name = "Calories",
                        value = f"**{Decimal(obj.calories * (multiplier ** 3)):,.3}** calories\n")
    if obj.price is not None:
        embed.add_field(name = "Price",
                        value = f"**${Decimal(obj.price * (multiplier ** 3)):,.2}**")
    if obj.weight:
        embed.add_field(name = "Weight",
                        value = f"**{WV(obj.weight * (multiplier ** 3)):,.3mu}**")

    return embed

def relativestatsembed(obj: DigiObject, userdata: userdb.User) -> Embed:
    embed = _get_stats_embed(obj, userdata.viewscale)
    embed.title = obj.name + " *[relative]*"
    embed.description = (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                            f"To {userdata.nickname}, {obj.article} {obj.name} looks...\n")
    return embed

def relativestatssentence(obj: DigiObject, userdata: userdb.User) -> str:
    return (f"{userdata.nickname} is {userdata.height:,.3{userdata.unitsystem}} tall."
            f" To them, {obj.article} {obj.name} looks ") \
        + get_stats_sentence(obj, userdata.viewscale, userdata.unitsystem)

def statsembed(obj: DigiObject) -> Embed:
    embed = _get_stats_embed(obj)
    embed.title = obj.name
    embed.description = f"*{obj.note}*" if obj.note else None
    return embed
    
def get_stats_sentence(obj: DigiObject, multiplier: Decimal, system: Literal["m", "u"]) -> str:
    statsstrings: list[str] = []
    if obj.height:
        statsstrings.append(f"**{SV(obj.height * multiplier):,.3{system}}** tall")
    if obj.length:
        statsstrings.append(f"**{SV(obj.length * multiplier):,.3{system}}** long")
    if obj.width:
        statsstrings.append(f"**{SV(obj.width * multiplier):,.3{system}}** wide")
    if obj.diameter:
        statsstrings.append(f"**{SV(obj.diameter * multiplier):,.3{system}}** across")
    if obj.depth:
        statsstrings.append(f"**{SV(obj.depth * multiplier):,.3{system}}** deep")
    if obj.thickness:
        statsstrings.append(f"**{SV(obj.thickness * multiplier):,.3{system}}** thick")
    if obj.calories is not None:
        statsstrings.append(f"has **{Decimal(obj.calories * (multiplier ** 3)):,.3}** calories")
    if obj.price is not None:
        statsstrings.append(f"costs **USD ${Decimal(obj.price * (multiplier ** 3)):,.2f}**")
    if obj.weight:
        statsstrings.append(f"weighs **{WV(obj.weight * multiplier ** 3):,.3{system}}**")

    returnstr = sentence_join(statsstrings, oxford=True) + "."

    return returnstr

def add_obj_to_units(obj: DigiObject):
    if obj.unitlength is not None:
        u = Unit(
            factor=Decimal(obj.unitlength),
            name=obj.name,
            namePlural=obj.name_plural,
            names=obj.aliases,
            symbol=obj.symbol
        )
        SV.add_unit(u)
        SV.add_system_unit("o", SystemUnit(u))

    if obj.weight is not None:
        u = Unit(
            factor=Decimal(obj.weight),
            name=obj.name,
            namePlural=obj.name_plural,
            names=obj.aliases,
            symbol=obj.symbol
        )
        WV.add_unit(u)
        WV.add_system_unit("o", SystemUnit(u))


def load_obj_file(filename: str):
    fileJson = json.loads(pkg_resources.read_text(sizebot.data.objects, filename))
    load_obj_json(fileJson)


def load_obj_json(data: list[ObjectJson]):
    for d in data:
        objects.append(DigiObject.from_json(d))


def init():
    global objects, food, land, tags

    for filename in pkg_resources.contents(sizebot.data.objects):
        if filename.endswith(".json"):
            load_obj_file(filename)

    objects.sort()
    for o in objects:
        add_obj_to_units(o)

    # cached values
    food = [o for o in objects if "food" in o.tags]
    land = [o for o in objects if "land" in o.tags]
    for o in objects:
        for tag in o._tags:
            if tag not in tags:
                tags[tag] = 1
            else:
                tags[tag] += 1


def get_close_object_smart(val: SV | WV) -> DigiObject:
    """This is a "smart" algorithm meant for use in &lookslike and &keypoints.

    Tries to get a single object for comparison, prioritizing integer closeness.
    """
    best_dict: dict[Decimal, list[tuple[Decimal, tuple[Decimal, Decimal], DigiObject]]] = {
        Decimal(0.5): [],
        Decimal(1): [],
        Decimal(1.5): [],
        Decimal(2): [],
        Decimal(2.5): [],
        Decimal(3): [],
        Decimal(4): [],
        Decimal(5): [],
        Decimal(6): []
    }

    dists: list[tuple[Decimal, tuple[Decimal, Decimal], DigiObject]] = []
    for obj in objects:
        if "nc" in obj.tags:
            continue
        if isinstance(val, WV) and obj.weight is not None:
            ratio = val / obj.weight
        elif isinstance(val, SV):
            ratio = val / obj.unitlength
        else:
            continue
        ratio_semi = round(ratio, 1)
        rounded_ratio = round(ratio)

        intness = 2 * (ratio - rounded_ratio)

        oneness = (1 - ratio if ratio > 1 else 1 / ratio - 1)

        dist = intness**2 + oneness**2

        p = (dist, (oneness, intness), obj)
        if ratio_semi in best_dict:
            best_dict[ratio_semi].append(p)
        else:
            dists.append(p)

    best: list[tuple[Decimal, tuple[Decimal, Decimal], DigiObject]] = []
    for at_val in best_dict.values():
        best.extend(at_val)
        if len(best) >= 10:
            break
    else:
        dists = sorted(dists, key=lambda p: p[0])
        best.extend(dists[:10])

    possible_objects = best[:10]
    return random.choice(possible_objects)[-1]


def format_close_object_smart(val: SV | WV) -> str:
    obj = get_close_object_smart(val)
    if isinstance(val, WV) and obj.weight is not None:
        ans = round(val / obj.weight, 1)
    elif isinstance(val, SV):
        ans = round(val / obj.unitlength, 1)
    else:
        raise TypeError

    return f"{ans:.1f} {obj.name_plural if ans != 1 else obj.name}"
