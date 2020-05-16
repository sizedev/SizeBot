import json
import re
from copy import copy
from functools import total_ordering
from typing import Literal

from sizebot import conf
from sizebot.lib import errors
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import isURL

# Defaults
defaultheight = SV("1.754")  # meters
defaultweight = WV("66760")  # grams


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["guildid", "id", "nickname", "_picture_url", "description", "_gender", "display", "_height",
                 "_baseheight", "_baseweight", "_footlength", "_hairlength", "_taillength", "_unitsystem",
                 "species", "soft_gender", "avatar_url"]

    def __init__(self):
        self.guildid = None
        self.id = None
        self.nickname = None
        self._picture_url = None
        self.description = None
        self._gender = None
        self.display = True
        self._height = defaultheight
        self._baseheight = defaultheight
        self._baseweight = defaultweight
        self._footlength = None
        self._hairlength = None
        self._taillength = None
        self._unitsystem = "m"
        self.species = None
        self.soft_gender = None
        self.avatar_url = None

    def __str__(self):
        return (f"GUILDID `{self.guildid}`, ID `{self.id}`, NICK `{self.nickname}`, GEND `{self.gender}`, "
                f"DISP `{self.display}`, CHEI `{self.height}`, BHEI `{self.baseheight}`, BWEI `{self.baseweight}`, "
                f"FOOT `{self.footlength}`, HAIR `{self.hairlength}`, TAIL `{self.taillength}`, "
                f"UNIT `{self.unitsystem}`, SPEC `{self.species}`")

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def picture_url(self):
        return self._picture_url

    @picture_url.setter
    def picture_url(self, value):
        if not isURL(value):
            raise ValueError(f"{value} is not a valid URL.")
        self._picture_url = value

    @property
    def auto_picture_url(self):
        return self.picture_url or self.avatar_url

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
    def taillength(self):
        return self._taillength

    @taillength.setter
    def taillength(self, value):
        if value is None:
            self._taillength = None
            return
        self._taillength = SV(max(0, SV(value)))

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
        return self.gender or self.soft_gender or "m"

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

    def formattedscale(self):
        """For printing scale in strings."""
        if self.scale < 0.1:
            return f"1:{1/self.scale:,.0}"
        elif self.scale < 1:
            return f"1:{1/self.scale:,.1}"
        else:
            return f"{self.scale:,.3}x"

    @property
    def tag(self):
        if self.id is not None:
            tag = f"<@{self.id}>"
        else:
            tag = self.nickname
        return tag

    def getFormattedScale(self, scaletype: Literal["height", "weight"] = "height", verbose = False):
        if scaletype == "height":
            reversescale = 1 / self.scale
            if reversescale > 10:
                if verbose:
                    return f"{self.scale:,.3}x (1:{reversescale:,.0})"
                else:
                    return f"1:{reversescale:,.0}"
            elif reversescale > 1:
                if verbose:
                    return f"{self.scale:,.3}x (1:{reversescale:,.1})"
                else:
                    return f"1:{reversescale:,.1}"
            else:
                return f"{self.scale:,.3}x"
        elif scaletype == "weight":
            weightscale = self.scale ** 3
            reverseweightscale = 1 / weightscale
            if reverseweightscale > 10:
                if verbose:
                    return f"{weightscale:,.3}x (1:{reverseweightscale:,.0})"
                else:
                    return f"1:{reverseweightscale:,.0}"
            elif reverseweightscale > 1:
                if verbose:
                    return f"{weightscale:,.3}x (1:{reverseweightscale:,.1})"
                else:
                    return f"1:{reverseweightscale:,.1}"
            else:
                return f"{weightscale:,.3}x"

    # Return an python dictionary for json exporting
    def toJSON(self):
        return {
            "guildid": self.guildid,
            "id": self.id,
            "nickname": self.nickname,
            "picture_url": self.picture_url,
            "description": self.description,
            "gender": self.gender,
            "display": self.display,
            "height": str(self.height),
            "baseheight": str(self.baseheight),
            "baseweight": str(self.baseweight),
            "footlength": None if self.footlength is None else str(self.footlength),
            "hairlength": None if self.hairlength is None else str(self.hairlength),
            "taillength": None if self.taillength is None else str(self.taillength),
            "unitsystem": self.unitsystem,
            "species": self.species
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.guildid = jsondata.get("guildid", 350429009730994199)  # Default to Size Matters.
        userdata.id = jsondata["id"]
        userdata.nickname = jsondata["nickname"]
        userdata.picture_url = jsondata.get("picture_url")
        userdata.description = jsondata.get("description")
        userdata.gender = jsondata.get("gender")
        userdata.display = jsondata["display"]
        userdata.height = jsondata["height"]
        userdata.baseheight = jsondata["baseheight"]
        userdata.baseweight = jsondata["baseweight"]
        userdata.footlength = jsondata.get("footlength")
        userdata.hairlength = jsondata.get("hairlength")
        userdata.taillength = jsondata.get("taillength")
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


def load(guildid, userid, *, member=None):
    path = getUserPath(guildid, userid)
    try:
        with open(path, "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException(guildid, userid)
    user = User.fromJSON(jsondata)
    if member:
        if not user.gender:
            user.soft_gender = member.gender
        user.avatar_url = member.avatar_url

    return user


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


def countprofiles():
    usercount = len(list(conf.guilddbpath.glob("*/users/*.json")))
    return usercount


def countusers():
    userlist = list(conf.guilddbpath.glob("*/users/*.json"))
    userids = []
    for user in userlist:
        m = re.match(r"\/users\/(.*)\.json", user)
        if m:
            userids.append(m.group(1))
    usercount = len(set(userids))
    return usercount


def listUsers(guildid = None):
    userfiles = conf.guilddbpath.glob("*/users/*.json")
    users = [(int(p.parent.parent.name), int(p.stem)) for p in userfiles]
    return users
