from functools import total_ordering
import importlib.resources as pkg_resources
import json
import random
from typing import Literal

from discord import Embed

import sizebot.data.objects
from sizebot import __version__
from sizebot.lib import errors
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.language import getPlural, getIndefiniteArticle
from sizebot.lib.units import SV, WV, Unit, SystemUnit
from sizebot.lib.utils import removeprefix, sentence_join

objects: list["DigiObject"] = []
food: list["DigiObject"] = []
tags: dict[str, int] = {}


@total_ordering
class DigiObject:
    def __init__(self, name, dimension, aliases=[], tags=[], symbol = None, height = None, length = None,
                 width = None, diameter = None, depth = None, thickness = None, calories = None,
                 weight = None, note = None):

        self.name = name
        self.dimension = dimension
        self.namePlural = getPlural(name)
        self.singularNames = aliases + [self.name]
        self.aliases = aliases + [getPlural(a) for a in aliases]
        self.aliases = self.aliases + [a.replace("™", "").replace("®", "") for a in self.aliases + [self.name]]  # Remove ®, ™
        self.aliases = list(set(self.aliases))  # Remove duplicates
        self.tags = tags + [getPlural(t) for t in tags]
        self.article = getIndefiniteArticle(self.name).split(" ")[0]
        self.symbol = symbol or None
        self.note = note or None

        self.height = height and SV(height)
        self.length = length and SV(length)
        self.width = width and SV(width)
        self.diameter = diameter and SV(diameter)
        self.depth = depth and SV(depth)
        self.thickness = thickness and SV(thickness)
        self.calories = SV(calories) if calories is not None else None
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

        self.unitlength = getattr(self, dimensionmap[dimension])

    @property
    def image(self):
        # TODO: See issue #153.
        return None

    def addToUnits(self):
        if self.unitlength is not None:
            SV.addUnit(Unit(factor=self.unitlength, name=self.name, namePlural=self.namePlural,
                            names=self.aliases, symbol = self.symbol))
            SV.addSystemUnit("o", SystemUnit(self.name))

        if self.weight is not None:
            WV.addUnit(Unit(factor=self.weight, name=self.name, namePlural=self.namePlural,
                            names=self.aliases, symbol = self.symbol))
            WV.addSystemUnit("o", SystemUnit(self.name))

    def getStats(self, multiplier = 1):
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
        if self.weight:
            returnstr += "and weighs...\n"
            returnstr += f"{emojis.blank}**{WV(self.weight * (multiplier ** 3)):,.3mu}**"
        return returnstr

    def getStatsSentence(self, multiplier = 1, system: Literal["m", "u"] = "m"):
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
            statsstrings.append(f"has **{Decimal(self.calories * (multiplier ** 3)):,.3}** calories\n")
        if self.weight:
            statsstrings.append(f"weighs **{WV(self.weight * multiplier ** 3):,.3{system}}**")

        returnstr = sentence_join(statsstrings, oxford=True) + "."

        return returnstr

    def getStatsEmbed(self, multiplier = 1):
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
        if self.calories is not None:
            embed.add_field(name = "Calories",
                            value = f"has **{Decimal(self.calories * (multiplier **3)):,.3}** calories\n")
        if self.weight:
            embed.add_field(name = "Weight",
                            value = f"**{WV(self.weight * (multiplier ** 3)):,.3mu}**")

        if self.image:
            embed.set_image(self.image)

        return embed

    def stats(self):
        return f"{self.article.capitalize()} {self.name} is...\n" + self.getStats()

    def statsembed(self):
        embed = self.getStatsEmbed()
        embed.title = self.name
        embed.description = f"*{self.note}*" if self.note else None
        return embed

    def relativestats(self, userdata):
        return (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                f"To {userdata.nickname}, {self.article} {self.name} looks...\n") \
            + self.getStats(userdata.viewscale)

    def relativestatssentence(self, userdata):
        return (f"{userdata.nickname} is {userdata.height:,.3{userdata.unitsystem}} tall."
                f" To them, {self.article} {self.name} looks ") \
            + self.getStatsSentence(userdata.viewscale, userdata.unitsystem)

    def relativestatsembed(self, userdata):
        embed = self.getStatsEmbed(userdata.viewscale)
        embed.title = self.name + " *[relative]*"
        embed.description = (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                             f"To {userdata.nickname}, {self.article} {self.name} looks...\n")
        return embed

    def __eq__(self, other):
        if isinstance(other, str):
            lowerName = other.lower()
            return lowerName == self.name.lower() \
                or lowerName == self.namePlural \
                or lowerName in (n.lower() for n in self.aliases)
        return super().__eq__(other)

    def __lt__(self, other):
        if isinstance(other, DigiObject):
            return self.unitlength < other.unitlength
        return self.unitlength < other

    @classmethod
    def findByName(cls, name):
        lowerName = name.lower()
        for o in objects:
            if o == lowerName:
                return o
        name = removeprefix(name, "random").strip()
        tagged = [o for o in objects if name in o.tags]
        if tagged:
            return random.choice(tagged)
        return None

    @classmethod
    def fromJson(cls, objJson):
        return cls(**objJson)

    @classmethod
    async def convert(cls, ctx, argument):
        obj = cls.findByName(argument)
        if obj is None:
            raise errors.InvalidObject(argument)
        return obj

    def __str__(self):
        return self.name

    def __repr__(self) -> str:
        return str(self)


def loadObjFile(filename):
    try:
        fileJson = json.loads(pkg_resources.read_text(sizebot.data.objects, filename))
    except FileNotFoundError:
        fileJson = None
    loadObjJson(fileJson)


def loadObjJson(fileJson):
    for objJson in fileJson:
        objects.append(DigiObject.fromJson(objJson))


def init():
    for filename in pkg_resources.contents(sizebot.data.objects):
        if filename.endswith(".json"):
            loadObjFile(filename)
    for o in objects:
        o.addToUnits()

    # cached values
    global food, tags
    food = [o for o in objects if "food" in o.tags]
    for o in objects:
        for tag in o.tags:
            if tag not in tags:
                tags[tag] = 1
            else:
                tags[tag] += 1
