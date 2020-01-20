import json

from copy import copy
from sizebot import conf
from sizebot.digidecimal import Decimal
from sizebot.lib import errors, utils
from sizebot.lib.units import SV, WV

# Defaults
defaultheight = SV("1.754")  # meters
defaultweight = WV("66760")  # grams

# Map the deprecated user array constants to the new names
#                      NICK        DISP       CHEI      BHEI          BWEI          UNIT          SPEC
DEPRECATED_NAME_MAP = ["nickname", "display", "height", "baseheight", "baseweight", "unitsystem", "species"]


class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id", "nickname", "_gender", "display", "_height", "_baseheight", "_baseweight", "_footlength", "_unitsystem", "species"]

    def __init__(self):
        self.id = None
        self.nickname = None
        self._gender = None
        self.display = True
        self._height = defaultheight
        self._baseheight = defaultheight
        self._baseweight = defaultweight
        self._footlength = None
        self._unitsystem = "m"
        self.species = None

    def __str__(self):
        return f"ID {self.id}, NICK {self.nickname}, GEND {self.gender}, DISP {self.display}, CHEI {self.height}, BHEI {self.baseheight}, BWEI {self.baseweight}, FOOT {self.footlength}, UNIT {self.unitsystem}, SPEC {self.species}"

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = SV(utils.clamp(0, SV(value), SV.infinity))

    @property
    def baseheight(self):
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value):
        self._baseheight = SV(utils.clamp(0, SV(value), SV.infinity))

    @property
    def footlength(self):
        return self._footlength

    @footlength.setter
    def footlength(self, value):
        if value is None:
            self._footlength = None
            return
        self._footlength = utils.clamp(0, SV(value), SV.infinity)

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
        self._baseweight = WV(utils.clamp(0, WV(value), WV.infinity))

    @property
    def weight(self):
        return WV(self.baseweight / (self.viewscale ** Decimal("3")))

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
        self.height = self.baseheight / viewscale

    @property
    def scale(self):
        """How scaled up the user looks to the world"""
        return self.height / self.baseheight

    @scale.setter
    def scale(self, scale):
        """Scale the user height to match the scale"""
        self.height = self.baseheight * scale

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
            "id": self.id,
            "nickname": self.nickname,
            "gender": self.gender,
            "display": self.display,
            "height": str(self.height),
            "baseheight": str(self.baseheight),
            "baseweight": str(self.baseweight),
            "footlength": None if self.footlength is None else str(self.footlength),
            "unitsystem": self.unitsystem,
            "species": self.species
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.id = jsondata["id"]
        userdata.nickname = jsondata["nickname"]
        userdata.gender = jsondata.get("gender")
        userdata.display = jsondata["display"]
        userdata.height = jsondata["height"]
        userdata.baseheight = jsondata["baseheight"]
        userdata.baseweight = jsondata["baseweight"]
        userdata.footlength = jsondata.get("footlength")
        userdata.unitsystem = jsondata["unitsystem"]
        userdata.species = jsondata["species"]
        return userdata

    def __lt__(self, other):
        return self.height < other.height

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


def getuserpath(userid):
    return conf.userdbpath / f"{userid}.json"


def save(userdata):
    userid = userdata.id
    if userid is None:
        raise errors.CannotSaveWithoutIDException
    conf.userdbpath.mkdir(exist_ok = True)
    jsondata = userdata.toJSON()
    with open(getuserpath(userid), "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(userid):
    try:
        with open(getuserpath(userid), "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException
    return User.fromJSON(jsondata)


def delete(userid):
    getuserpath(userid).unlink(missing_ok = True)


# TODO: Set this up as a User's __nonzero__ function
# e.g.: bool(user) = user.id.exists()
def exists(userid):
    exists = True
    try:
        load(userid)
    except errors.UserNotFoundException:
        exists = False
    return exists


def count():
    usercount = len(list(conf.userdbpath.glob("*.json")))
    return usercount
