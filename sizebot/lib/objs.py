from functools import total_ordering
import importlib.resources as pkg_resources
import json
import math
import random
from typing import Literal, Optional

from discord import Embed

import sizebot.data.objects
from sizebot import __version__
from sizebot.lib import errors, userdb
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.language import get_plural, get_indefinite_article
from sizebot.lib.units import AV, SV, VV, WV, Unit, SystemUnit
from sizebot.lib.utils import removeprefix, sentence_join

objects: list["DigiObject"] = []
food: list["DigiObject"] = []
land: list["DigiObject"] = []
tags: dict[str, int] = {}


@total_ordering
class DigiObject:
    def __init__(self, name, dimension, aliases=[], tags=[], symbol = None, height = None, length = None,
                 width = None, diameter = None, depth = None, thickness = None, calories = None, price = None,
                 weight = None, note = None):

        self.name = name
        self.dimension = dimension
        self.name_plural = get_plural(name)
        self.singular_names = aliases + [self.name]
        self.aliases = aliases + [get_plural(a) for a in aliases]
        self.aliases = self.aliases + [a.replace("™", "").replace("®", "") for a in self.aliases + [self.name]]  # Remove ®, ™
        self.aliases = list(set(self.aliases))  # Remove duplicates
        self._tags = tags
        self.tags = tags + [get_plural(t) for t in self._tags]
        self.article = get_indefinite_article(self.name).split(" ")[0]
        self.symbol = symbol or None
        self.note = note or None

        self.height = height and SV(height)
        self.length = length and SV(length)
        self.width = width and SV(width)
        self.diameter = diameter and SV(diameter)
        self.depth = depth and SV(depth)
        self.thickness = thickness and SV(thickness)
        self.calories = SV(calories) if calories is not None else None
        self.price = Decimal(price) if price is not None else None
        self.weight = weight and WV(weight)

        dimensionmap = {
            "h": "height",
            "l": "length",
            "w": "width",
            "d": "diameter",
            "p": "depth",
            "t": "thickness",
            "c": "calories",
        }

        self.unitlength: SV = getattr(self, dimensionmap[dimension])

    @property
    def image(self):
        # TODO: See issue #153.
        return None

    @property
    def area(self) -> Optional[AV]:
        if self.height is not None and self.width is not None:
            return AV(self.height * self.width)
        elif self.length is not None and self.width is not None:
            return AV(self.length * self.width)
        elif self.diameter:
            r = self.diameter / 2
            r2 = r ** 2
            return AV(math.pi * r2)
        return None

    @property
    def volume(self) -> Optional[VV]:
        if self.area is not None:
            if self.depth is not None:
                return VV(self.area * self.depth)
            elif self.thickness is not None:
                return VV(self.area * self.thickness)
        return None

    def add_to_units(self):
        if self.unitlength is not None:
            SV.add_unit(Unit(factor=self.unitlength, name=self.name, namePlural=self.name_plural,
                             names=self.aliases, symbol = self.symbol))
            SV.add_system_unit("o", SystemUnit(self.name))

        if self.weight is not None:
            WV.add_unit(Unit(factor=self.weight, name=self.name, namePlural=self.name_plural,
                             names=self.aliases, symbol = self.symbol))
            WV.add_system_unit("o", SystemUnit(self.name))

    def get_stats(self, multiplier = 1):
        returnstr = ""
        if self.height:
            returnstr += f"{emojis.blank}**{SV(self.height * multiplier):,.3mu}** tall\n"
        if self.length:
            returnstr += f"{emojis.blank}**{SV(self.length * multiplier):,.3mu}** long\n"
        if self.width:
            returnstr += f"{emojis.blank}**{SV(self.width * multiplier):,.3mu}** wide\n"
        if self.diameter:
            returnstr += f"{emojis.blank}**{SV(self.diameter * multiplier):,.3mu}** across\n"
        if self.depth:
            returnstr += f"{emojis.blank}**{SV(self.depth * multiplier):,.3mu}** deep\n"
        if self.thickness:
            returnstr += f"{emojis.blank}**{SV(self.thickness * multiplier):,.3mu}** thick\n"
        if self.calories is not None:
            returnstr += f"{emojis.blank}has **{Decimal(self.calories * (multiplier ** 3)):,.3}** calories\n"
        if self.price is not None:
            returnstr += f"{emojis.blank}costs **${Decimal(self.price * (multiplier ** 3)):,.2}**\n"
        if self.weight:
            returnstr += "and weighs...\n"
            returnstr += f"{emojis.blank}**{WV(self.weight * (multiplier ** 3)):,.3mu}**"
        return returnstr

    def get_stats_sentence(self, multiplier = 1, system: Literal["m", "u"] = "m"):
        statsstrings = []
        if self.height:
            statsstrings.append(f"**{SV(self.height * multiplier):,.3{system}}** tall")
        if self.length:
            statsstrings.append(f"**{SV(self.length * multiplier):,.3{system}}** long")
        if self.width:
            statsstrings.append(f"**{SV(self.width * multiplier):,.3{system}}** wide")
        if self.diameter:
            statsstrings.append(f"**{SV(self.diameter * multiplier):,.3{system}}** across")
        if self.depth:
            statsstrings.append(f"**{SV(self.depth * multiplier):,.3{system}}** deep")
        if self.thickness:
            statsstrings.append(f"**{SV(self.thickness * multiplier):,.3{system}}** thick")
        if self.calories is not None:
            statsstrings.append(f"has **{Decimal(self.calories * (multiplier ** 3)):,.3}** calories")
        if self.price is not None:
            statsstrings.append(f"costs **${Decimal(self.price * (multiplier ** 3)):,.2}**")
        if self.weight:
            statsstrings.append(f"weighs **{WV(self.weight * multiplier ** 3):,.3{system}}**")

        returnstr = sentence_join(statsstrings, oxford=True) + "."

        return returnstr

    def get_stats_embed(self, multiplier = 1):
        embed = Embed()
        embed.set_author(name = f"SizeBot {__version__}")

        if self.height:
            embed.add_field(name = "Height",
                            value = f"**{SV(self.height * multiplier):,.3mu}** tall\n")
        if self.length:
            embed.add_field(name = "Length",
                            value = f"**{SV(self.length * multiplier):,.3mu}** long\n")
        if self.width:
            embed.add_field(name = "Width",
                            value = f"**{SV(self.width * multiplier):,.3mu}** wide\n")
        if self.diameter:
            embed.add_field(name = "Diameter",
                            value = f"**{SV(self.diameter * multiplier):,.3mu}** across\n")
        if self.depth:
            embed.add_field(name = "Depth",
                            value = f"**{SV(self.depth * multiplier):,.3mu}** deep\n")
        if self.thickness:
            embed.add_field(name = "Thickness",
                            value = f"**{SV(self.thickness * multiplier):,.3mu}** thick\n")
        if self.area is not None:
            embed.add_field(name = "Area",
                            value = f"**{AV(self.area * (multiplier ** 2)):,.3mu}**\n")
        if self.volume is not None:
            embed.add_field(name = "Volume",
                            value = f"**{VV(self.volume * (multiplier ** 3)):,.3mu}**\n")
        if self.calories is not None:
            embed.add_field(name = "Calories",
                            value = f"**{Decimal(self.calories * (multiplier ** 3)):,.3}** calories\n")
        if self.price is not None:
            embed.add_field(name = "Price",
                            value = f"**${Decimal(self.price * (multiplier ** 3)):,.2}**")
        if self.weight:
            embed.add_field(name = "Weight",
                            value = f"**{WV(self.weight * (multiplier ** 3)):,.3mu}**")

        if self.image:
            embed.set_image(self.image)

        return embed

    def stats(self):
        return f"{self.article.capitalize()} {self.name} is...\n" + self.get_stats()

    def statsembed(self):
        embed = self.get_stats_embed()
        embed.title = self.name
        embed.description = f"*{self.note}*" if self.note else None
        return embed

    def relativestats(self, userdata: userdb.User):
        return (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                f"To {userdata.nickname}, {self.article} {self.name} looks...\n") \
            + self.get_stats(userdata.viewscale)

    def relativestatssentence(self, userdata: userdb.User):
        return (f"{userdata.nickname} is {userdata.height:,.3{userdata.unitsystem}} tall."
                f" To them, {self.article} {self.name} looks ") \
            + self.get_stats_sentence(userdata.viewscale, userdata.unitsystem)

    def relativestatsembed(self, userdata: userdb.User):
        embed = self.get_stats_embed(userdata.viewscale)
        embed.title = self.name + " *[relative]*"
        embed.description = (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                             f"To {userdata.nickname}, {self.article} {self.name} looks...\n")
        return embed

    def __eq__(self, other):
        if isinstance(other, str):
            lowerName = other.lower()
            return lowerName == self.name.lower() \
                or lowerName == self.name_plural \
                or lowerName in (n.lower() for n in self.aliases)
        elif isinstance(other, DigiObject):
            return (self.name, self.unitlength) == (other.name, other.unitlength)
        return super().__eq__(other)

    def __lt__(self, other):
        if isinstance(other, DigiObject):
            return self.unitlength < other.unitlength
        return self.unitlength < other

    @classmethod
    def find_by_name(cls, name):
        lowerName = name.lower()
        for o in objects:
            if o == lowerName:
                return o
        lowerName = removeprefix(lowerName, "random").strip()
        tagged = [o for o in objects if lowerName in o.tags]
        if tagged:
            return random.choice(tagged)
        return None

    @classmethod
    def from_JSON(cls, objJson):
        return cls(**objJson)

    @classmethod
    async def convert(cls, ctx, argument):
        obj = cls.find_by_name(argument)
        if obj is None:
            raise errors.InvalidObject(argument)
        return obj

    def __str__(self):
        return self.name

    def __repr__(self) -> str:
        return str(self)


def load_obj_file(filename):
    try:
        fileJson = json.loads(pkg_resources.read_text(sizebot.data.objects, filename))
    except FileNotFoundError:
        fileJson = None
    load_obj_JSON(fileJson)


def load_obj_JSON(fileJson):
    for objJson in fileJson:
        objects.append(DigiObject.from_JSON(objJson))


def init():
    global objects, food, land, tags

    for filename in pkg_resources.contents(sizebot.data.objects):
        if filename.endswith(".json"):
            load_obj_file(filename)

    objects.sort()
    for o in objects:
        o.add_to_units()

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
    best_dict: dict[float, list] = {
        1.0: [],
        0.5: [],
        2.0: [],
        1.5: [],
        3.0: [],
        2.5: [],
        4.0: [],
        5.0: [],
        6.0: []
    }

    weight = isinstance(val, WV)

    val = float(val)

    dists = []
    for obj in objects:
        if weight and not obj.weight:
            continue
        ratio = val / float(obj.unitlength) if not weight else val / float(obj.weight)
        ratio_semi = round(ratio, 1)
        rounded_ratio = round(ratio)

        intness = 2.0 * (ratio - rounded_ratio)

        oneness = (1.0 - ratio if ratio > 1.0 else 1.0 / ratio - 1.0)

        dist = intness**2 + oneness**2

        p = (dist, (oneness, intness), obj)
        if ratio_semi in best_dict:
            best_dict[ratio_semi].append(p)
        else:
            dists.append(p)

    best = []
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
    weight = isinstance(val, WV)
    obj = get_close_object_smart(val)
    ans = round(val / obj.unitlength, 1) if not weight else round(val / obj.weight, 1)
    return f"{ans:.1f} {obj.name_plural if ans != 1 else obj.name}"
