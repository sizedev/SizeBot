import json
from pathlib import Path
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

# Map the deprecated user array constants to the new names
DEPRECATED_NAME_MAP = ["nickname", "display", "height", "baseheight", "baseweight", "density", "unitsystem", "species"]

userdbpath = Path("json_test")


class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id", "nickname", "display", "height", "baseheight", "baseweight", "density", "unitsystem", "species"]

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
        attrname = DEPRECATED_NAME_MAP[key]
        return getattr(self, attrname)

    def __setitem__(self, key, value):
        attrname = DEPRECATED_NAME_MAP[key]
        return setattr(self, attrname, value)

    def __str__(self):
        return f"ID {self.id}, NICK {self.nickname}, DISP {self.display}, CHEI {self.height}, BHEI {self.baseheight}, BWEI {self.baseweight}, DENS {self.density}, UNIT {self.unitsystem}, SPEC {self.species}"

    def toJSON(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "display": self.display,
            "height": str(self.height),
            "baseheight": str(self.baseheight),
            "baseweight": str(self.baseweight),
            "density": str(self.density),
            "unitsystem": self.unitsystem,
            "species": self.species
        }

    @classmethod
    def fromJSON(cls, jsondata):
        user = User()
        user.id = jsondata["id"]
        user.nickname = jsondata["nickname"]
        user.display = jsondata["display"]
        user.height = Decimal(jsondata["height"])
        user.baseheight = Decimal(jsondata["baseheight"])
        user.baseweight = Decimal(jsondata["baseweight"])
        user.density = Decimal(jsondata["density"])
        user.unitsystem = jsondata["unitsystem"]
        user.species = jsondata["species"]
        return user


def save(user):
    userdbpath.mkdir(exist_ok = True)
    jsondata = user.toJSON()
    id = user.id
    with open(userdbpath / f"{id}.json", "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(id):
    with open(userdbpath / f"{id}.json", "r") as f:
        jsondata = json.load(f)
    return User.fromJSON(jsondata)
