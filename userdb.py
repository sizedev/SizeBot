import json
from pathlib import Path
from decimal import Decimal
import digierror as errors

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
defaultheight = Decimal("1.754")  # meters
defaultweight = Decimal("66760")  # grams
defaultdensity = Decimal("1.0")

# Map the deprecated user array constants to the new names
DEPRECATED_NAME_MAP = ["nickname", "display", "height", "baseheight", "baseweight", "density", "unitsystem", "species"]

userdbpath = Path("../users")


class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id", "nickname", "display", "_height", "_baseheight", "_baseweight", "_density", "_unitsystem", "species"]

    def __init__(self):
        self.id = None
        self.nickname = None
        self.display = True
        self._height = defaultheight
        self._baseheight = defaultheight
        self._baseweight = defaultweight
        self._density = defaultdensity
        self._unitsystem = "m"
        self.species = None

    def __str__(self):
        return f"ID {self.id}, NICK {self.nickname}, DISP {self.display}, CHEI {self.height}, BHEI {self.baseheight}, BWEI {self.baseweight}, DENS {self.density}, UNIT {self.unitsystem}, SPEC {self.species}"

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = Decimal(value)

    @property
    def baseheight(self):
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value):
        self._baseheight = Decimal(value)

    @property
    def baseweight(self):
        return self._baseweight

    @baseweight.setter
    def baseweight(self, value):
        self._baseweight = Decimal(value)

    @property
    def density(self):
        return self._density

    @density.setter
    def density(self, value):
        self._density = Decimal(value)

    # Check that unitsystem is valid and lowercase
    @property
    def unitsystem(self):
        return self._unitsystem

    @unitsystem.setter
    def unitsystem(self, value):
        value = value.lower()
        if value not in ["m", "u"]:
            raise ValueError(f"Invalid unitsystem: '{value}'")
        self._unitsystem = value

    # Act like an array for legacy usage
    def __getitem__(self, key):
        attrname = DEPRECATED_NAME_MAP[key]
        return getattr(self, attrname)

    def __setitem__(self, key, value):
        attrname = DEPRECATED_NAME_MAP[key]
        return setattr(self, attrname, value)

    # Return an python dictionary for json exporting
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

    # Create a new object from a python dictionary imported using json
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
    id = user.id
    if id is None:
        errors.throw(errors.CANNOT_SAVE_WITHOUT_ID)
    userdbpath.mkdir(exist_ok = True)
    jsondata = user.toJSON()
    with open(userdbpath / f"{id}.json", "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(id):
    try:
        with open(userdbpath / f"{id}.json", "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException(id)
    return User.fromJSON(jsondata)


def count():
    usercount = len(list(userdbpath.glob("*.json")))
    return usercount
