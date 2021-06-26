import json
from copy import copy
from functools import total_ordering
import importlib.resources as pkg_resources
from typing import Dict, List, Literal, Optional

import arrow
from arrow.arrow import Arrow

import sizebot.data
from sizebot.lib import errors, paths
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff, Rate as ParseableRate
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import isURL, truncate

# Defaults
defaultheight = SV("1.754")            # meters
defaultweight = WV("66760")            # grams
defaultterminalvelocity = SV("63.63")  # meters/second
falllimit = SV("7.73")                 # meters/second
defaultliftstrength = WV("18143.7")    # grams

modelJSON = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["guildid", "id", "nickname", "lastactive", "_picture_url", "description", "_gender", "display",
                 "_height", "_baseheight", "_baseweight", "_footlength", "_pawtoggle", "_furtoggle",
                 "_hairlength", "_taillength", "_earheight", "_liftstrength", "triggers", "_unitsystem", "species", "soft_gender",
                 "avatar_url", "_walkperhour", "_runperhour", "_swimperhour", "incomprehensible",
                 "_currentscalestep", "_currentscaletalk", "scaletalklock",
                 "currentmovetype", "movestarted",
                 "registration_steps_remaining", "_macrovision_model", "_macrovision_view"]

    def __init__(self):
        self.guildid: int = None
        self.id: int = None
        self.nickname: str = None
        self._picture_url: Optional[str] = None
        self.description: Optional[str] = None
        self._gender: Optional[str] = None
        self.display: bool = True
        self._height: SV = defaultheight
        self._baseheight: SV = defaultheight
        self._baseweight: SV = defaultweight
        self._footlength: Optional[SV] = None
        self._pawtoggle: bool = False
        self._furtoggle: bool = False
        self._hairlength: Optional[SV] = None
        self._taillength: Optional[SV] = None
        self._earheight: Optional[SV] = None
        self._liftstrength: Optional[WV] = None
        self._walkperhour: Optional[ParseableRate] = None
        self._runperhour: Optional[ParseableRate] = None
        self._swimperhour: Optional[ParseableRate] = None
        self.incomprehensible: bool = False
        self._currentscalestep: Optional[Diff] = None
        self._currentscaletalk: Optional[Diff] = None
        self.scaletalklock: bool = False
        self.currentmovetype: Optional[str] = None
        self.movestarted: Optional[Arrow] = None
        self.triggers: Dict[str, Diff] = {}
        self._unitsystem: str = "m"
        self.species: Optional[str] = None
        self.soft_gender = None
        self.avatar_url: Optional[str] = None
        self.lastactive: Arrow = None
        self.registration_steps_remaining: List[str] = []
        self._macrovision_model: Optional[str] = None
        self._macrovision_view: Optional[str] = None

    def __str__(self):
        return (f"<User GUILDID = {self.guildid!r}, ID = {self.id!r}, NICKNAME = {self.nickname!r} ...>")

    def __repr__(self):
        desc = None if self.description is None else truncate(self.description, 50)
        return (f"<User GUILDID = {self.guildid!r}, ID = {self.id!r}, NICKNAME = {self.nickname!r}, PICTURE_URL = {self.picture_url!r}, "
                f"DESCRIPTION = {desc}, DISPLAY = {self.display!r}, "
                f"HEIGHT = {self.height!r}, BASEHEIGHT = {self.baseheight!r}, "
                f"WEIGHT = {self.weight!r}, BASEWEIGHT = {self.baseweight!r}, "
                f"FOOTLENGTH = {self.footlength!r}, HAIRLENGTH = {self.hairlength!r}, "
                f"TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r}, LIFTSTRENGTH = {self.liftstrength!r}, "
                f"PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}, SWIMPERHOUR = {self.swimperhour!r}, INCOMPREHENSIBLE = {self.incomprehensible!r}, "
                f"CURRENTSCALESTEP = {self.currentscalestep!r}, CURRENTSCALETALK = {self.currentscaletalk!r}, "
                f"CURRENTMOVETYPE = {self.currentmovetype!r}, MOVESTARTED = {self.movestarted!r}, "
                f"TRIGGERS = {self.triggers!r}, "
                f"UNITSYSTEM = {self.unitsystem!r}, SPECIES = {self.species!r}, SOFT_GENDER = {self.soft_gender!r}, "
                f"AVATAR_URL = {self.avatar_url!r}, LASTACTIVE = {self.lastactive!r}, IS_ACTIVE = {self.is_active!r}, "
                f"REGISTRATION_STEPS_REMAINING = {self.registration_steps_remaining!r}, REGISTERED = {self.registered!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}>")

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
        value = SV(value)
        if value < 0:
            value = SV(0)
        self._height = value

    @property
    def baseheight(self):
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value):
        value = SV(value)
        if value < 0:
            value = SV(0)
        self._baseheight = value

    @property
    def footlength(self):
        return self._footlength

    @footlength.setter
    def footlength(self, value):
        if value is None or SV(value) <= 0:
            self._footlength = None
            return
        self._footlength = SV(value)

    @property
    def pawtoggle(self):
        return self._pawtoggle

    @pawtoggle.setter
    def pawtoggle(self, value):
        self._pawtoggle = bool(value)

    @property
    def furtoggle(self):
        return self._furtoggle

    @furtoggle.setter
    def furtoggle(self, value):
        self._furtoggle = bool(value)

    @property
    def footname(self):
        return "Paw" if self.pawtoggle else "Foot"

    @property
    def hairname(self):
        return "Fur" if self.furtoggle else "Hair"

    @property
    def hairlength(self):
        return self._hairlength

    @hairlength.setter
    def hairlength(self, value):
        if value is None:
            self._hairlength = None
            return
        value = SV(value)
        if value < 0:
            value = SV(0)
        self._hairlength = value

    @property
    def taillength(self):
        return self._taillength

    @taillength.setter
    def taillength(self, value):
        if value is None or SV(value) <= 0:
            self._taillength = None
            return
        self._taillength = SV(value)

    @property
    def earheight(self):
        return self._earheight

    @earheight.setter
    def earheight(self, value):
        if value is None or SV(value) <= 0:
            self._earheight = None
            return
        self._earheight = SV(value)

    @property
    def liftstrength(self):
        return self._liftstrength

    @liftstrength.setter
    def liftstrength(self, value):
        if value is None:
            self._liftstrength = None
            return
        value = WV(value)
        if value < 0:
            value = WV(0)
        self._liftstrength = value

    @property
    def walkperhour(self):
        return self._walkperhour

    @walkperhour.setter
    def walkperhour(self, value):
        if value is None:
            self._walkperhour = None
            return

        if isinstance(value, ParseableRate):
            if value.diff.changetype != "add":
                raise ValueError("Invalid rate for speed parsing.")
            if value.diff.amount < 0:
                raise ValueError("Speed can not go backwards!")
            value = value.diff.amount / value.time * Decimal("3600")

        value = SV(value)

        if value < 0:
            value = SV(0)

        self._walkperhour = value

    @property
    def runperhour(self):
        return self._runperhour

    @runperhour.setter
    def runperhour(self, value):
        if value is None:
            self._runperhour = None
            return

        if isinstance(value, ParseableRate):
            if value.diff.changetype != "add":
                raise ValueError("Invalid rate for speed parsing.")
            if value.diff.amount < 0:
                raise ValueError("Speed can not go backwards!")
            value = value.diff.amount / value.time * Decimal("3600")

        value = SV(value)

        if value < 0:
            value = SV(0)

        self._runperhour = value

    @property
    def climbperhour(self):  # Essentially temp, since we're fixing this in BetterStats
        return SV(Decimal(4828) / self.viewscale)

    @property
    def crawlperhour(self):  # Essentially temp, since we're fixing this in BetterStats
        return SV(Decimal(2556) / self.viewscale)

    @property
    def swimperhour(self):
        return self._swimperhour

    @swimperhour.setter
    def swimperhour(self, value):
        if value is None:
            self._swimperhour = None
            return

        if isinstance(value, ParseableRate):
            if value.diff.changetype != "add":
                raise ValueError("Invalid rate for speed parsing.")
            if value.diff.amount < 0:
                raise ValueError("Speed can not go backwards!")
            value = value.diff.amount / value.time * Decimal("3600")

        value = SV(value)

        if value < 0:
            value = SV(0)

        self._swimperhour = value

    @property
    def currentscalestep(self):
        return self._currentscalestep

    @currentscalestep.setter
    def currentscalestep(self, value):
        if value is None:
            self._currentscalestep = None
            return

        if not isinstance(value, Diff):
            raise ValueError("Input was not a Diff.")

        self._currentscalestep = value

    @property
    def currentscaletalk(self):
        return self._currentscaletalk

    @currentscaletalk.setter
    def currentscaletalk(self, value):
        if value is None:
            self._currentscaletalk = None
            return

        if not isinstance(value, Diff):
            raise ValueError("Input was not a Diff.")

        self._currentscaletalk = value

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
        value = WV(value)
        if value < 0:
            value = WV(0)
        self._baseweight = value

    @property
    def weight(self):
        return WV(self.baseweight * (self.scale ** 3))

    @weight.setter
    def weight(self, value):
        self.baseweight = value * (self.viewscale ** 3)

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

    @property
    def registered(self):
        return len(self.registration_steps_remaining) == 0

    def complete_step(self, step):
        was_completed = self.registered
        try:
            self.registration_steps_remaining.remove(step)
        except ValueError:
            pass
        is_completed = self.registered
        just_completed = (not was_completed) and is_completed
        return just_completed

    @property
    def macrovision_model(self):
        if self._macrovision_model is not None:
            return self._macrovision_model
        return "Human"

    @macrovision_model.setter
    def macrovision_model(self, value):
        if value not in modelJSON.keys():
            raise errors.InvalidMacrovisionModelException(value)
        self._macrovision_model = value

    @property
    def macrovision_view(self):
        if self._macrovision_view is not None:
            return self._macrovision_view
        human_views = {
            "m": "male",
            "f": "female",
            None: "male"
        }
        return human_views[self.gender]

    @macrovision_view.setter
    def macrovision_view(self, value):
        if value not in modelJSON[self.macrovision_model].keys():
            raise errors.InvalidMacrovisionViewException(self.macrovision_model, value)
        self._macrovision_view = value

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
            "guildid":          str(self.guildid),
            "id":               str(self.id),
            "nickname":         self.nickname,
            "lastactive":       None if self.lastactive is None else self.lastactive.isoformat(),
            "picture_url":      self.picture_url,
            "description":      self.description,
            "gender":           self.gender,
            "display":          self.display,
            "height":           str(self.height),
            "baseheight":       str(self.baseheight),
            "baseweight":       str(self.baseweight),
            "footlength":       None if self.footlength is None else str(self.footlength),
            "pawtoggle":        self.pawtoggle,
            "furtoggle":        self.furtoggle,
            "hairlength":       None if self.hairlength is None else str(self.hairlength),
            "taillength":       None if self.taillength is None else str(self.taillength),
            "earheight":        None if self.earheight is None else str(self.earheight),
            "liftstrength":     None if self.liftstrength is None else str(self.liftstrength),
            "walkperhour":      None if self.walkperhour is None else str(self.walkperhour),
            "runperhour":       None if self.runperhour is None else str(self.runperhour),
            "swimperhour":      None if self.swimperhour is None else str(self.swimperhour),
            "incomprehensible": self.incomprehensible,
            "currentscalestep": None if self.currentscalestep is None else self.currentscalestep.toJSON(),
            "currentscaletalk": None if self.currentscaletalk is None else self.currentscaletalk.toJSON(),
            "scaletalklock":    self.scaletalklock,
            "currentmovetype":  self.currentmovetype,
            "movestarted":      None if self.movestarted is None else self.movestarted.isoformat(),
            "triggers":         {k: v.toJSON() for k, v in self.triggers.items()},
            "unitsystem":       self.unitsystem,
            "species":          self.species,
            "registration_steps_remaining": self.registration_steps_remaining,
            "macrovision_model": self._macrovision_model,
            "macrovision_view": self._macrovision_view
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        userdata = User()
        userdata.guildid = jsondata.get("guildid", 350429009730994199)  # Default to Size Matters.
        userdata.id = int(jsondata["id"])
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
        userdata.pawtoggle = jsondata.get("pawtoggle", False)
        userdata.furtoggle = jsondata.get("furtoggle", False)
        userdata.hairlength = jsondata.get("hairlength")
        userdata.taillength = jsondata.get("taillength")
        userdata.earheight = jsondata.get("earheight")
        userdata.liftstrength = jsondata.get("liftstrength")
        userdata.walkperhour = jsondata.get("walkperhour")
        userdata.runperhour = jsondata.get("runperhour")
        userdata.swimperhour = jsondata.get("swimperhour")
        userdata.incomprehensible = jsondata.get("incomprehensible", False)
        currentscalestep = jsondata.get("currentscalestep")
        if currentscalestep is not None:
            currentscalestep = Diff.fromJSON(currentscalestep)
        userdata.currentscalestep = currentscalestep
        currentscaletalk = jsondata.get("currentscaletalk")
        if currentscaletalk is not None:
            currentscaletalk = Diff.fromJSON(currentscaletalk)
        userdata.currentscaletalk = currentscaletalk
        userdata.scaletalklock = jsondata.get("scaletalklock")
        userdata.currentmovetype = jsondata.get("currentmovetype")
        movestarted = jsondata.get("movestarted")
        if movestarted is not None:
            movestarted = arrow.get(movestarted)
        userdata.movestarted = movestarted
        triggers = jsondata.get("triggers")
        if triggers is not None:
            triggers = {k: Diff.fromJSON(v) for k, v in triggers}
        else:
            triggers = {}
        userdata.triggers = triggers
        userdata.unitsystem = jsondata["unitsystem"]
        userdata.species = jsondata["species"]
        userdata.registration_steps_remaining = jsondata.get("registration_steps_remaining", [])
        userdata._macrovision_model = jsondata.get("macrovision_model")
        userdata._macrovision_view = jsondata.get("macrovision_view")
        return userdata

    def __lt__(self, other):
        return self.height < other.height

    def __eq__(self, other):
        return self.height == other.height

    def __add__(self, other):
        newuserdata = copy(self)
        newuserdata.height = self.height + other
        return newuserdata

    def __mul__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) * other
        return newuserdata

    def __div__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) / other
        return newuserdata

    def __pow__(self, other):
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) ** other
        return newuserdata


def getGuildUsersPath(guildid):
    return paths.guilddbpath / f"{guildid}" / "users"


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


def load(guildid, userid, *, member=None, allow_unreg=False):
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

    if (not allow_unreg) and (not user.registered):
        raise errors.UserNotFoundException(guildid, userid, unreg=True)

    return user


def delete(guildid, userid):
    path = getUserPath(guildid, userid)
    path.unlink(missing_ok = True)


def exists(guildid, userid, *, allow_unreg=False):
    exists = True
    try:
        load(guildid, userid, allow_unreg=allow_unreg)
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


def listUsers(*, guildid = None, userid = None):
    guildid = int(guildid) if guildid else "*"
    userid = int(userid) if userid else "*"
    userfiles = paths.guilddbpath.glob(f"{guildid}/users/{userid}.json")
    users = [(int(u.parent.parent.name), int(u.stem)) for u in userfiles]
    return users
