from decimal import Decimal

# Deprecated user array constants
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7

# Defaults
defaultheight = Decimal(1754000)  # micrometers
defaultweight = Decimal(66760000)  # milligrams
defaultdensity = Decimal(1.0)


class User:
    # __slots__ declares to python what attributes to expect. But since it's in the right order, we can also use it to look up attributes by the deprecated user info constants.
    __slots__ = ["nickname", "display", "height", "baseheight", "baseweight", "density", "unitsystem", "species", "id"]

    def __init__(self):
        self.id = None
        self.nickname = None
        self.display = True
        self.height = Decimal("1754000")
        self.baseheight = Decimal("1754000")
        self.baseweight = Decimal("66760000")
        self.density = Decimal("1")
        self.unitsystem = "m"
        self.species = ""

    def __getitem__(self, key):
        attrname = self.__slots__[key]
        return getattr(self, attrname)

    def __setitem__(self, key, value):
        attrname = self.__slots__[key]
        return setattr(self, attrname, value)


def save(user):
    pass


def load(id):
    pass
