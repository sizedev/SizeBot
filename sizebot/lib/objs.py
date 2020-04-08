import importlib.resources as pkg_resources
import json

import sizebot.data
from sizebot.lib import errors
from sizebot.lib.language import getPlural, getIndefiniteArticle
from sizebot.lib.units import SV, WV, Unit, SystemUnit

objects = []


class DigiObject:
    def __init__(self, name, aliases=[], length=None, height=None, width=None, depth=None, weight=None):
        self.name = name
        self.namePlural = getPlural(name)
        self.singularNames = aliases + [self.name]
        self.aliases = aliases + [getPlural(a) for a in aliases]
        self.article = getIndefiniteArticle(self.name).split(" ")[0]
        self.length = length and SV(length)
        self.height = height and SV(height)
        self.width = width and SV(width)
        self.depth = depth and SV(depth)
        self.weight = weight and WV(weight)

    def addToUnits(self):
        if self.length is not None:
            SV.addUnit(Unit(factor=self.length, name=self.name, namePlural=self.namePlural, names=self.aliases))
            SV.addSystemUnit("o", SystemUnit(self.name))
        if self.width is not None:
            SV.addUnit(Unit(factor=self.width, name=self.name, namePlural=self.namePlural, names=self.aliases))
            SV.addSystemUnit("o", SystemUnit(self.name))
        elif self.height is not None:
            SV.addUnit(Unit(factor=self.height, name=self.name, namePlural=self.namePlural, names=self.aliases))
            SV.addSystemUnit("o", SystemUnit(self.name))
        elif self.depth is not None:
            SV.addUnit(Unit(factor=self.depth, name=self.name, namePlural=self.namePlural, names=self.aliases))
            SV.addSystemUnit("o", SystemUnit(self.name))

        if self.weight is not None:
            WV.addUnit(Unit(factor=self.weight, name=self.name, namePlural=self.namePlural, names=self.aliases))
            WV.addSystemUnit("o", SystemUnit(self.name))

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
