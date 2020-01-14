import json
import importlib.resources as pkg_resources

from sizebot.digiSV import SV, WV, Unit, SystemUnit
from sizebot import units as units_dir

objects = []


class DigiObject:
    objects = []

    def __init__(self, name, namePlural=None, names=[], length=None, height=None, width=None, depth=None, weight=None):
        self.name = name
        self.namePlural = namePlural
        self.names = names
        self.length = length
        self.height = height
        self.width = width
        self.depth = depth
        self.weight = weight

    @classmethod
    def fromJson(cls, objJson):
        return cls(**objJson)

    def addToUnits(self):
        if self.length is not None:
            SV.addUnit(Unit(factor=self.length, name=self.name, namePlural=self.namePlural, names=self.names))
            SV.addSystemUnit("o", SystemUnit(self.name))
        if self.width is not None:
            SV.addUnit(Unit(factor=self.width, name=self.name, namePlural=self.namePlural, names=self.names))
            SV.addSystemUnit("o", SystemUnit(self.name))
        elif self.height is not None:
            SV.addUnit(Unit(factor=self.height, name=self.name, namePlural=self.namePlural, names=self.names))
            SV.addSystemUnit("o", SystemUnit(self.name))
        elif self.depth is not None:
            SV.addUnit(Unit(factor=self.depth, name=self.name, namePlural=self.namePlural, names=self.names))
            SV.addSystemUnit("o", SystemUnit(self.name))

        if self.weight is not None:
            WV.addUnit(Unit(factor=self.weight, name=self.name, namePlural=self.namePlural, names=self.names))
            WV.addSystemUnit("o", SystemUnit(self.name))


def loadObjFile(filename):
    try:
        fileJson = json.loads(pkg_resources.read_text(units_dir, filename))
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
