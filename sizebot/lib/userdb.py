import json
from copy import copy
from functools import total_ordering
from sizebot.lib.decimal import Decimal
from sizebot.lib.diff import Rate as ParseableRate
from typing import Literal

import arrow

from sizebot import conf
from sizebot.lib import errors
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import isURL

# Defaults
defaultheight = SV("1.754")            # meters
defaultweight = WV("66760")            # grams
defaultterminalvelocity = SV("63.63")  # meters/second
falllimit = SV("7.73")                 # meters/second
defaultliftstrength = WV("18143.7")    # grams


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["guildid", "id", "nickname", "lastactive", "_picture_url", "description", "_gender", "display",
                 "_height", "_baseheight", "_baseweight", "_footlength", "_hairlength", "_taillength",
                 "_liftstrength", "_unitsystem", "species", "soft_gender", "avatar_url"]

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
        self._liftstrength = None
        self._walkperhour = None
        self._runperhour = None
        self._unitsystem = "m"
        self.species = None
        self.soft_gender = None
        self.avatar_url = None
        self.lastactive = None

    def __str__(self):
        return (f"GUILDID `{self.guildid}`, ID `{self.id}`, NICK `{self.nickname}`, GEND `{self.gender}`, "
                f"DISP `{self.display}`, CHEI `{self.height}`, BHEI `{self.baseheight}`, BWEI `{self.baseweight}`, "
                f"FOOT `{self.footlength}`, HAIR `{self.hairlength}`, TAIL `{self.taillength}`, LIFT `{self.liftstrength}`, "
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
    def is_active(self):
        now = arrow.now()
        weekago = now.shift(weeks = -1)
        lastactive = self.lastactive
        if self.lastactive is None:
            return False
        return lastactive > weekago

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
        if value == 0:
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
        if value == 0:
            self._taillength = None
            return
        self._taillength = SV(max(0, SV(value)))

    @property
    def liftstrength(self):
        return self._liftstrength

    @liftstrength.setter
    def liftstrength(self, value):
        if value is None:
            self._liftstrength = None
            return
        self._liftstrength = WV(max(0, WV(value)))

    @property
    def walkperhour(self):
        return self._walkperhour

    @walkperhour.setter
    def walkperhour(self, value):
        if value is None:
            self._walkperhour = None
            return
        rate = ParseableRate.parse(value)

        if rate.diff.changetype != "add":
            raise ValueError("Invalid rate for speed parsing.")
        if rate.diff.amount < 0:
            raise ValueError("Speed can not go backwards!")

        dist = rate.diff.amount / rate.time * Decimal("3600")

        self._walkperhour = SV(max(0, SV(dist)))

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
        if value not in ["m", "u", "o"]:
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
            tag = f"<@!{self.id}>"
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
            "guildid":      self.guildid,
            "id":           self.id,
            "nickname":     self.nickname,
            "lastactive":   None if self.lastactive is None else self.lastactive.isoformat(),
            "picture_url":  self.picture_url,
            "description":  self.description,
            "gender":       self.gender,
            "display":      self.display,
            "height":       str(self.height),
            "baseheight":   str(self.baseheight),
            "baseweight":   str(self.baseweight),
            "footlength":   None if self.footlength is None else str(self.footlength),
            "hairlength":   None if self.hairlength is None else str(self.hairlength),
            "taillength":   None if self.taillength is None else str(self.taillength),
            "liftstrength": None if self.liftstrength is None else str(self.liftstrength),
            "walkperhour":  None if self.walkperhour is None else str(self.walkperhour),
            "runperhour":   None if self.runperhour is None else str(self.runperhour),
            "unitsystem":   self.unitsystem,
            "species":      self.species
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.guildid = jsondata.get("guildid", 350429009730994199)  # Default to Size Matters.
        userdata.id = jsondata["id"]
        userdata.nickname = jsondata["nickname"]
        lastactive = jsondata.get("lastactive")
        if lastactive is not None:
            lastactive = arrow.get(lastactive)
        userdata.lastactive = lastactive
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
        userdata.liftstrength = jsondata.get("liftstrength")
        userdata.walkperhour = jsondata.get("walkperhour")
        userdata.runperhour = jsondata.get("runperhour")
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
    users = listUsers()
    usercount = len(list(users))
    return usercount


def countusers():
    users = listUsers()
    usercount = len(set(u for g, u in users))
    return usercount


def listUsers(guildid = None):
    userfiles = conf.guilddbpath.glob("*/users/*.json")
    users = [(int(u.parent.parent.name), int(u.stem)) for u in userfiles]
    return users
