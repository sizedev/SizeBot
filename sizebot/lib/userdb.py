from copy import copy
import json
from functools import total_ordering

from sizebot import conf
from sizebot.lib import errors
from sizebot.lib.units import SV, WV

# Defaults
defaultheight = SV("1.754")  # meters
defaultweight = WV("66760")  # grams

# Map the deprecated user array constants to the new names
#                      NICK        DISP       CHEI      BHEI          BWEI          UNIT          SPEC
DEPRECATED_NAME_MAP = ["nickname", "display", "height", "baseheight", "baseweight", "unitsystem", "species"]


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["guildid", "id", "nickname", "_gender", "display", "_height", "_baseheight", "_baseweight", "_footlength", "_hairlength", "_unitsystem", "species"]

    def __init__(self):
        self.guildid = None
        self.id = None
        self.nickname = None
        self._gender = None
        self.display = True
        self._height = defaultheight
        self._baseheight = defaultheight
        self._baseweight = defaultweight
        self._footlength = None
        self._hairlength = None
        self._unitsystem = "m"
        self.species = None

    def __str__(self):
        return f"GUILDID {self.guildid}, ID {self.id}, NICK {self.nickname}, GEND {self.gender}, DISP {self.display}, CHEI {self.height}, BHEI {self.baseheight}, BWEI {self.baseweight}, FOOT {self.footlength}, HAIR {self.hairlength}, UNIT {self.unitsystem}, SPEC {self.species}"

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = SV(max(0, SV(value)))

    @property
    def baseheight(self):
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value):
        self._baseheight = SV(max(0, SV(value)))

    @property
    def footlength(self):
        return self._footlength

    @footlength.setter
    def footlength(self, value):
        if value is None:
            self._footlength = None
            return
        self._footlength = SV(max(0, SV(value)))

    @property
    def hairlength(self):
        return self._hairlength

    @hairlength.setter
    def hairlength(self, value):
        if value is None:
            self._hairlength = None
            return
        self._hairlength = SV(max(0, SV(value)))

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, value):
        if value is None:
            self._gender = None
            return
        value = value.lower()
        if value not in ["m", "f"]:
            raise ValueError(f"Unrecognized gender: '{value}'")
        self._gender = value

    @property
    def autogender(self):
        if self.gender:
            return self.gender
        # TODO: Search the roles for a gender.
        return "m"

    @property
    def baseweight(self):
        return self._baseweight

    @baseweight.setter
    def baseweight(self, value):
        self._baseweight = WV(max(0, WV(value)))

    @property
    def weight(self):
        return WV(self.baseweight * (self.scale ** 3))

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

    @property
    def viewscale(self):
        """How scaled up the world looks to this user"""
        return self.baseheight / self.height

    @viewscale.setter
    def viewscale(self, viewscale):
        """Scale the user height to match the view scale"""
        self.height = SV(self.baseheight / viewscale)

    @property
    def scale(self):
        """How scaled up the user looks to the world"""
        return self.height / self.baseheight

    @scale.setter
    def scale(self, scale):
        """Scale the user height to match the scale"""
        self.height = SV(self.baseheight * scale)

    @property
    def tag(self):
        if self.id is not None:
            tag = f"<@{self.id}>"
        else:
            tag = self.nickname
        return tag

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
            "guildid": self.guildid,
            "id": self.id,
            "nickname": self.nickname,
            "gender": self.gender,
            "display": self.display,
            "height": str(self.height),
            "baseheight": str(self.baseheight),
            "baseweight": str(self.baseweight),
            "footlength": None if self.footlength is None else str(self.footlength),
            "hairlength": None if self.hairlength is None else str(self.hairlength),
            "unitsystem": self.unitsystem,
            "species": self.species
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.guildid = jsondata.get("guildid", 350429009730994199)
        userdata.id = jsondata["id"]
        userdata.nickname = jsondata["nickname"]
        userdata.gender = jsondata.get("gender")
        userdata.display = jsondata["display"]
        userdata.height = jsondata["height"]
        userdata.baseheight = jsondata["baseheight"]
        userdata.baseweight = jsondata["baseweight"]
        userdata.footlength = jsondata.get("footlength")
        userdata.hairlength = jsondata.get("hairlength")
        userdata.unitsystem = jsondata["unitsystem"]
        userdata.species = jsondata["species"]
        return userdata

    def __lt__(self, other):
        return self.height < other.height

    def __eq__(self, other):
        return self.height == other.height

    # TODO: Add __add__, which has to be able to take Users or SVs or Decimals as "other".

    def __mul__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = self.scale * other
        return newuserdata

    def __div__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = self.scale / other
        return newuserdata

    def __pow__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = self.scale ** other
        return newuserdata


def getGuildUsersPath(guildid):
    return conf.guilddbpath / f"{guildid}" / "users"


def getUserPath(guildid, userid):
    return getGuildUsersPath(guildid) / f"{userid}.json"


def save(userdata):
    guildid = userdata.guildid
    userid = userdata.id
    if guildid is None or userid is None:
        raise errors.CannotSaveWithoutIDException
    path = getUserPath(guildid, userid)
    path.parent.mkdir(exist_ok = True, parents = True)
    jsondata = userdata.toJSON()
    with open(path, "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(guildid, userid):
    path = getUserPath(guildid, userid)
    try:
        with open(path, "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException(guildid, userid)
    return User.fromJSON(jsondata)


def delete(guildid, userid):
    path = getUserPath(guildid, userid)
    path.unlink(missing_ok = True)


# TODO: Set this up as a User's __nonzero__ function
# e.g.: bool(user) = user.id.exists()
def exists(guildid, userid):
    exists = True
    try:
        load(guildid, userid)
    except errors.UserNotFoundException:
        exists = False
    return exists


def count():
    usercount = len(list(conf.guilddbpath.glob("*/users/*.json")))
    return usercount


def listUsers(guildid = None):
    userfiles = conf.guilddbpath.glob("*/users/*.json")
    users = [(int(p.parent.parent.name), int(p.stem)) for p in userfiles]
    return users
