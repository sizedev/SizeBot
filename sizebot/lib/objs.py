import importlib.resources as pkg_resources
import json

import discord

import sizebot.data
from sizebot import __version__
from sizebot.lib import errors
from sizebot.lib.constants import emojis
from sizebot.lib.language import getPlural, getIndefiniteArticle
from sizebot.lib.units import SV, WV, Unit, SystemUnit

objects = []


class DigiObject:
    def __init__(self, name, dimension, aliases=[], symbol = None, height = None, length = None,
                 width = None, diameter = None, depth = None, thickness = None, weight = None):

        self.name = name
        self.namePlural = getPlural(name)
        self.singularNames = aliases + [self.name]
        self.aliases = aliases + [getPlural(a) for a in aliases]
        self.article = getIndefiniteArticle(self.name).split(" ")[0]
        self.symbol = symbol or None

        self.height = height and SV(height)
        self.length = length and SV(length)
        self.width = width and SV(width)
        self.diameter = diameter and SV(diameter)
        self.depth = depth and SV(depth)
        self.thickness = thickness and SV(thickness)
        self.weight = weight and WV(weight)

        dimensionmap = {
            "h": "height",
            "l": "length",
            "w": "width",
            "d": "diameter",
            "p": "depth",
            "t": "thickness"
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
            returnstr += f"{emojis.blank}**{SV(self.depth * multiplier):,.3mu}** thick\n"
        if self.weight:
            returnstr += "and weighs...\n"
            returnstr += f"{emojis.blank}**{WV(self.weight * (multiplier ** 3)):,.3mu}**"
        return returnstr

    def getStatsEmbed(self, multiplier = 1):
        embed = discord.Embed()
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
                            value = f"**{SV(self.depth * multiplier):,.3mu}** thick\n")
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
        return embed

    def relativestats(self, userdata):
        return (f"__{userdata.nickname} is {userdata.height:,.3mu} tall.__\n"
                f"To {userdata.nickname}, {self.article} {self.name} looks...\n") \
            + self.getStats(userdata.viewscale)

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

    @classmethod
    def findByName(cls, name):
        lowerName = name.lower()
        for o in objects:
            if o == lowerName:
                return o
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


def loadObjFile(filename):
    try:
        fileJson = json.loads(pkg_resources.read_text(sizebot.data, filename))
    except FileNotFoundError:
        fileJson = None
    loadObjJson(fileJson)


def loadObjJson(fileJson):
    for objJson in fileJson:
        objects.append(DigiObject.fromJson(objJson))


async def init():
    loadObjFile("objects.json")
    for o in objects:
        o.addToUnits()
