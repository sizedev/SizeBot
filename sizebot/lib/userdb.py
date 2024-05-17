from __future__ import annotations
from typing import Literal, TypedDict, Any

import re
import json
from copy import copy
from functools import total_ordering
import importlib.resources as pkg_resources
from pathlib import Path

import arrow
from arrow.arrow import Arrow

import discord
from discord.ext import commands

import sizebot.data
from sizebot.lib import errors, paths
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff, Rate
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.utils import is_url, truncate
from sizebot.lib.errors import InvalidSizeValue, InvalidStat
from sizebot.lib.shoesize import from_shoe_size
from sizebot.lib.utils import AliasMap, parse_scale, truthy

# Defaults
DEFAULT_HEIGHT = SV("1.754")            # meters
DEFAULT_WEIGHT = WV("66760")            # grams
FALL_LIMIT = SV("7.73")                 # meters/second
DEFAULT_LIFT_STRENGTH = WV("18143.7")   # grams

BASICALLY_ZERO = Decimal("1E-27")

modelJSON = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))

MoveTypeStr = Literal["walk", "run", "climb", "crawl", "swim"]


def str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    return str(v)


Gender = Literal["m", "f", "x"]


class PlayerStats(TypedDict):
    height: str
    weight: str
    footlength: str | None      # TODO: This is actually basefootlength (footlength at scale=1)
    pawtoggle: bool
    furtoggle: bool
    hairlength: str | None      # TODO: This is actually basehairlength (hairlength at scale=1)
    taillength: str | None      # TODO: This is actually basetaillength (taillength at scale=1)
    earheight: str | None       # TODO: This is actually baseearheight (earheight at scale=1)
    liftstrength: str | None    # TODO: This is actually baseliftstrength (liftstrength at scale=1)
    walkperhour: str | None     # TODO: This is actually basewalkperhour (walkperhour at scale=1)
    swimperhour: str | None     # TODO: This is actually baseswimperhour (swimperhour at scale=1)
    runperhour: str | None      # TODO: This is actually baserunperhour (runperhour at scale=1)
    gender: Gender | None
    nickname: str
    id: str
    macrovision_model: str | None
    macrovision_view: str | None


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = [
        "guildid", "id", "nickname", "lastactive", "_picture_url", "description", "_gender", "display",
        "_height", "_baseheight", "_baseweight", "_footlength", "_pawtoggle", "_furtoggle",
        "_hairlength", "_taillength", "_earheight", "_liftstrength", "triggers", "_unitsystem", "species", "soft_gender",
        "avatar_url", "_walkperhour", "_runperhour", "_swimperhour", "incomprehensible",
        "_currentscalestep", "_currentscaletalk", "scaletalklock",
        "currentmovetype", "movestarted", "movestop",
        "registration_steps_remaining", "_macrovision_model", "_macrovision_view",
        "button", "tra_reports", "allowchangefromothers"
    ]

    def __init__(self):
        self.guildid: int = None
        self.id: int = None
        self.nickname: str = None
        self._picture_url: str | None = None
        self.description: str | None = None
        self._gender: str | None = None
        self.display: bool = True
        self._height: SV = DEFAULT_HEIGHT
        self._baseheight: SV = DEFAULT_HEIGHT
        self._baseweight: SV = DEFAULT_WEIGHT
        self._footlength: SV | None = None
        self._pawtoggle: bool = False
        self._furtoggle: bool = False
        self._hairlength: SV | None = None
        self._taillength: SV | None = None
        self._earheight: SV | None = None
        self._liftstrength: WV | None = None
        self._walkperhour: Rate | None = None
        self._runperhour: Rate | None = None
        self._swimperhour: Rate | None = None
        self.incomprehensible: bool = False
        self._currentscalestep: Diff | None = None
        self._currentscaletalk: Diff | None = None
        self.scaletalklock: bool = False
        self.currentmovetype: MoveTypeStr | None = None
        self.movestarted: Arrow | None = None
        self.movestop: TV | None = None
        self.triggers: dict[str, Diff] = {}
        self.button: Diff | None = None
        self.tra_reports = 0
        self._unitsystem: str = "m"
        self.species: str | None = None
        self.soft_gender: str | None = None
        self.avatar_url: str | None = None
        self.lastactive: Arrow = None
        self.registration_steps_remaining: list[str] = []
        self._macrovision_model: str | None = None
        self._macrovision_view: str | None = None
        self.allowchangefromothers: bool | None = None

    def __str__(self) -> str:
        return (f"<User GUILDID = {self.guildid!r}, ID = {self.id!r}, NICKNAME = {self.nickname!r} ...>")

    def __repr__(self) -> str:
        desc = None if self.description is None else truncate(self.description, 50)
        return (f"<User GUILDID = {self.guildid!r}, ID = {self.id!r}, NICKNAME = {self.nickname!r}, PICTURE_URL = {self.picture_url!r}, "
                f"DESCRIPTION = {desc}, DISPLAY = {self.display!r}, "
                f"HEIGHT = {self.height!r}, BASEHEIGHT = {self.baseheight!r}, "
                f"WEIGHT = {self.weight!r}, BASEWEIGHT = {self.baseweight!r}, "
                f"FOOTLENGTH = {self.footlength!r}, HAIRLENGTH = {self.hairlength!r}, "
                f"TAILLENGTH = {self.taillength!r}, EARHEIGHT = {self.earheight!r}, LIFTSTRENGTH = {self.liftstrength!r}, "
                f"PAWTOGGLE = {self.pawtoggle!r}, FURTOGGLE = {self.furtoggle!r}, "
                f"WALKPERHOUR = {self.walkperhour!r}, RUNPERHOUR = {self.runperhour!r}, SWIMPERHOUR = {self.swimperhour!r}, "
                f"CURRENTSCALESTEP = {self.currentscalestep!r}, CURRENTSCALETALK = {self.currentscaletalk!r}, "
                f"CURRENTMOVETYPE = {self.currentmovetype!r}, MOVESTARTED = {self.movestarted!r}, MOVESTOP = {self.movestop!r}, "
                f"TRIGGERS = {self.triggers!r}, BUTTON = {self.button!r}, TRA_REPORTS = {self.tra_reports!r}, "
                f"UNITSYSTEM = {self.unitsystem!r}, SPECIES = {self.species!r}, SOFT_GENDER = {self.soft_gender!r}, "
                f"AVATAR_URL = {self.avatar_url!r}, LASTACTIVE = {self.lastactive!r}, IS_ACTIVE = {self.is_active!r}, "
                f"REGISTRATION_STEPS_REMAINING = {self.registration_steps_remaining!r}, REGISTERED = {self.registered!r}, "
                f"MACROVISION_MODEL = {self.macrovision_model!r}, MACROVISION_VIEW = {self.macrovision_view!r}>, "
                f"ALLOWCHANGEFROMOTHERS = {self.allowchangefromothers!r}")

    # Setters/getters to automatically force numeric values to be stored as Decimal
    @property
    def picture_url(self) -> str | None:
        return self._picture_url

    @picture_url.setter
    def picture_url(self, value: str | None):
        if not is_url(value):
            raise ValueError(f"{value} is not a valid URL.")
        self._picture_url = value

    @property
    def auto_picture_url(self) -> str | None:
        return self.picture_url or self.avatar_url

    @property
    def is_active(self) -> bool:
        now = arrow.now()
        weekago = now.shift(weeks = -1)
        lastactive = self.lastactive
        if self.lastactive is None:
            return False
        return lastactive > weekago

    @property
    def height(self) -> SV:
        return self._height

    @height.setter
    def height(self, value: SV):
        value = SV(value)
        if value < BASICALLY_ZERO:
            value = SV(0)
        self._height = value

    @property
    def baseheight(self) -> SV:
        return self._baseheight

    @baseheight.setter
    def baseheight(self, value: SV):
        value = SV(value)
        if value < BASICALLY_ZERO:
            value = SV(0)
        self._baseheight = value

    @property
    def footlength(self) -> SV | None:
        """Base foot length"""
        return self._footlength

    @footlength.setter
    def footlength(self, value: SV | None):
        if value is None or SV(value) < BASICALLY_ZERO:
            self._footlength = None
            return
        self._footlength = SV(value)

    @property
    def pawtoggle(self) -> bool:
        return self._pawtoggle

    @pawtoggle.setter
    def pawtoggle(self, value: bool):
        self._pawtoggle = bool(value)

    @property
    def furtoggle(self) -> bool:
        return self._furtoggle

    @furtoggle.setter
    def furtoggle(self, value: bool):
        self._furtoggle = bool(value)

    @property
    def footname(self) -> str:
        return "Paw" if self.pawtoggle else "Foot"

    @property
    def hairname(self) -> str:
        return "Fur" if self.furtoggle else "Hair"

    @property
    def hairlength(self) -> SV | None:
        """Base hair length"""
        return self._hairlength

    @hairlength.setter
    def hairlength(self, value: SV | None):
        if value is None:
            self._hairlength = None
            return
        value = SV(value)
        if value < BASICALLY_ZERO:
            value = SV(0)
        self._hairlength = value

    @property
    def taillength(self) -> SV | None:
        return self._taillength

    @taillength.setter
    def taillength(self, value: SV | None):
        if value is None or SV(value) <= BASICALLY_ZERO:
            self._taillength = None
            return
        self._taillength = SV(value)

    @property
    def earheight(self) -> SV | None:
        return self._earheight

    @earheight.setter
    def earheight(self, value: SV | None):
        if value is None or SV(value) <= BASICALLY_ZERO:
            self._earheight = None
            return
        self._earheight = SV(value)

    @property
    def liftstrength(self) -> SV | None:
        return self._liftstrength

    @liftstrength.setter
    def liftstrength(self, value: WV | None):
        if value is None:
            self._liftstrength = None
            return
        value = WV(value)
        if value < 0:
            value = WV(0)
        self._liftstrength = value

    @property
    def walkperhour(self) -> Rate | None:
        return self._walkperhour

    @walkperhour.setter
    def walkperhour(self, value: Rate | None):
        if value is None:
            self._walkperhour = None
            return

        if isinstance(value, Rate):
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
    def runperhour(self) -> Rate | None:
        return self._runperhour

    @runperhour.setter
    def runperhour(self, value: Rate | None):
        if value is None:
            self._runperhour = None
            return

        if isinstance(value, Rate):
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
    def climbperhour(self) -> SV:  # Essentially temp, since we're fixing this in BetterStats
        return SV(Decimal(4828) * self.scale)

    @property
    def crawlperhour(self) -> SV:  # Essentially temp, since we're fixing this in BetterStats
        return SV(Decimal(2556) * self.scale)

    @property
    def swimperhour(self) -> Rate | None:
        return self._swimperhour

    @swimperhour.setter
    def swimperhour(self, value: Rate | None):
        if value is None:
            self._swimperhour = None
            return

        if isinstance(value, Rate):
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
    def currentscalestep(self) -> Diff | None:
        return self._currentscalestep

    @currentscalestep.setter
    def currentscalestep(self, value: Diff | None):
        if value is None:
            self._currentscalestep = None
            return

        if not isinstance(value, Diff):
            raise ValueError("Input was not a Diff.")

        self._currentscalestep = value

    @property
    def currentscaletalk(self) -> Diff | None:
        return self._currentscaletalk

    @currentscaletalk.setter
    def currentscaletalk(self, value: Diff | None):
        if value is None:
            self._currentscaletalk = None
            return

        if not isinstance(value, Diff):
            raise ValueError("Input was not a Diff.")

        self._currentscaletalk = value

    @property
    def gender(self) -> str:
        return self._gender

    @gender.setter
    def gender(self, value: str):
        if value is None:
            self._gender = None
            return
        value = value.lower()
        if value not in ["m", "f"]:
            raise ValueError(f"Unrecognized gender: '{value}'")
        self._gender = value

    @property
    def autogender(self) -> str:
        return self.gender or self.soft_gender or "m"

    @property
    def baseweight(self) -> SV:
        return self._baseweight

    @baseweight.setter
    def baseweight(self, value: WV):
        value = WV(value)
        if value < 0:
            value = WV(0)
        self._baseweight = value

    @property
    def weight(self) -> WV:
        return WV(self.baseweight * (self.scale ** 3))

    @weight.setter
    def weight(self, value: WV):
        self.baseweight = value * (self.viewscale ** 3)

    # Check that unitsystem is valid and lowercase
    @property
    def unitsystem(self) -> str:
        return self._unitsystem

    @unitsystem.setter
    def unitsystem(self, value: str):
        value = value.lower()
        if value not in ["m", "u", "o"]:
            raise ValueError(f"Invalid unitsystem: '{value}'")
        self._unitsystem = value

    @property
    def viewscale(self) -> Decimal:
        """How scaled up the world looks to this user"""
        return self.baseheight / self.height

    @viewscale.setter
    def viewscale(self, viewscale: Decimal):
        """Scale the user height to match the view scale"""
        self.height = SV(self.baseheight / viewscale)

    @property
    def scale(self) -> Decimal:
        """How scaled up the user looks to the world"""
        return self.height / self.baseheight

    @scale.setter
    def scale(self, scale: Decimal):
        """Scale the user height to match the scale"""
        self.height = SV(self.baseheight * scale)

    @property
    def stats(self) -> PlayerStats:
        """A bit of a patchwork solution for transitioning to BetterStats."""
        return {
            "height": str_or_none(self.baseheight),
            "weight": str_or_none(self.baseweight),
            "footlength": str_or_none(self.footlength),
            "pawtoggle": self.pawtoggle,
            "furtoggle": self.furtoggle,
            "hairlength": str_or_none(self.hairlength),
            "taillength": str_or_none(self.taillength),
            "earheight": str_or_none(self.earheight),
            "liftstrength": str_or_none(self.liftstrength),
            "walkperhour": str_or_none(self.walkperhour),
            "swimperhour": str_or_none(self.swimperhour),
            "runperhour": str_or_none(self.runperhour),
            "gender": str_or_none(self.gender),     # TODO: Should this be autogender?
            "scale": str_or_none(self.scale),
            "nickname": str_or_none(self.nickname),
            "id": str_or_none(self.id),
            "macrovision_model": str_or_none(self.macrovision_model),
            "macrovision_view": str_or_none(self.macrovision_view)
        }

    @property
    def tag(self) -> str:
        if self.id is not None:
            tag = f"<@!{self.id}>"
        else:
            tag = self.nickname
        return tag

    @property
    def registered(self) -> bool:
        return len(self.registration_steps_remaining) == 0

    def complete_step(self, step: str) -> bool:
        was_completed = self.registered
        try:
            self.registration_steps_remaining.remove(step)
        except ValueError:
            pass
        is_completed = self.registered
        just_completed = (not was_completed) and is_completed
        return just_completed

    @property
    def macrovision_model(self) -> str:
        if self._macrovision_model is not None:
            return self._macrovision_model
        return "Human"

    @macrovision_model.setter
    def macrovision_model(self, value: str):
        if value not in modelJSON.keys():
            raise errors.InvalidMacrovisionModelException(value)
        self._macrovision_model = value

    @property
    def macrovision_view(self) -> str:
        if self._macrovision_view is not None:
            return self._macrovision_view
        human_views = {
            "m": "male",
            "f": "female",
            None: "male"
        }
        return human_views[self.autogender]

    @macrovision_view.setter
    def macrovision_view(self, value: str):
        if value not in modelJSON[self.macrovision_model].keys():
            raise errors.InvalidMacrovisionViewException(self.macrovision_model, value)
        self._macrovision_view = value

    # Return an python dictionary for json exporting
    def toJSON(self) -> Any:
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
            "incomprehensible": False,
            "currentscalestep": None if self.currentscalestep is None else self.currentscalestep.toJSON(),
            "currentscaletalk": None if self.currentscaletalk is None else self.currentscaletalk.toJSON(),
            "scaletalklock":    self.scaletalklock,
            "currentmovetype":  self.currentmovetype,
            "movestarted":      None if self.movestarted is None else self.movestarted.isoformat(),
            "movestop":         None if self.movestop is None else str(self.movestop),
            "triggers":         {k: v.toJSON() for k, v in self.triggers.items()},
            "button":           None if self.button is None else self.button.toJSON(),
            "tra_reports":      self.tra_reports,
            "unitsystem":       self.unitsystem,
            "species":          self.species,
            "registration_steps_remaining": self.registration_steps_remaining,
            "macrovision_model": self._macrovision_model,
            "macrovision_view": self._macrovision_view,
            "allowchangefromothers": self.allowchangefromothers
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata: dict) -> User:
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
        userdata.incomprehensible = False
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

        movestop = jsondata.get("movestop")
        if movestop is not None:
            movestop = TV(movestop)
        userdata.movestop = movestop

        triggers = jsondata.get("triggers")
        if triggers is not None:
            triggers = {k: Diff.fromJSON(v) for k, v in triggers.items()}
        else:
            triggers = {}
        userdata.triggers = triggers

        button = jsondata.get("button")
        if button is not None:
            button = Diff.fromJSON(button)
        userdata.button = button
        userdata.tra_reports = jsondata.get("tra_reports", 0)
        if userdata.tra_reports is None:
            userdata.tra_reports = 0
        userdata.unitsystem = jsondata["unitsystem"]
        userdata.species = jsondata["species"]
        userdata.registration_steps_remaining = jsondata.get("registration_steps_remaining", [])
        userdata._macrovision_model = jsondata.get("macrovision_model")
        userdata._macrovision_view = jsondata.get("macrovision_view")
        userdata.allowchangefromothers = jsondata.get("allowchangefromothers", False)
        return userdata

    def __lt__(self, other: User) -> bool:
        return self.height < other.height

    def __eq__(self, other: User) -> bool:
        return self.height == other.height

    def __add__(self, other: SV) -> User:
        newuserdata = copy(self)
        newuserdata.height = self.height + other
        return newuserdata

    def __mul__(self, other: Decimal) -> User:
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) * other
        return newuserdata

    def __div__(self, other: Decimal) -> User:
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) / other
        return newuserdata

    def __pow__(self, other: Decimal) -> User:
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) ** other
        return newuserdata


def get_guild_users_path(guildid: int) -> Path:
    return paths.guilddbpath / f"{guildid}" / "users"


def get_user_path(guildid: int, userid: int) -> Path:
    return get_guild_users_path(guildid) / f"{userid}.json"


def save(userdata: User):
    guildid = userdata.guildid
    userid = userdata.id
    if guildid is None or userid is None:
        raise errors.CannotSaveWithoutIDException
    path = get_user_path(guildid, userid)
    path.parent.mkdir(exist_ok = True, parents = True)
    jsondata = userdata.toJSON()
    with open(path, "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(guildid: int, userid: int, *, member: discord.Member = None, allow_unreg: bool = False) -> User:
    path = get_user_path(guildid, userid)
    try:
        with open(path, "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.UserNotFoundException(guildid, userid)
    user = User.fromJSON(jsondata)
    if member:
        if not user.gender:
            user.soft_gender = member.gender
        user.avatar_url = member.avatar

    if (not allow_unreg) and (not user.registered):
        raise errors.UserNotFoundException(guildid, userid, unreg=True)

    return user


def delete(guildid: int, userid: int):
    path = get_user_path(guildid, userid)
    path.unlink(missing_ok = True)


def exists(guildid: int, userid: int, *, allow_unreg: bool = False) -> bool:
    exists = True
    try:
        load(guildid, userid, allow_unreg=allow_unreg)
    except errors.UserNotFoundException:
        exists = False
    return exists


def count_profiles() -> int:
    users = list_users()
    usercount = len(list(users))
    return usercount


def count_users() -> int:
    users = list_users()
    usercount = len(set(u for g, u in users))
    return usercount


def list_users(*, guildid: int | None = None, userid: int | None = None) -> list[tuple[int, int]]:
    guildid = int(guildid) if guildid else "*"
    userid = int(userid) if userid else "*"
    userfiles = paths.guilddbpath.glob(f"{guildid}/users/{userid}.json")
    users = [(int(u.parent.parent.name), int(u.stem)) for u in userfiles]
    return users


def load_or_fake(memberOrSV: discord.Member | FakePlayer | SV, nickname: str | None = None, *, allow_unreg: bool = False) -> User:
    if isinstance(memberOrSV, discord.Member):
        return load(memberOrSV.guild.id, memberOrSV.id, member=memberOrSV, allow_unreg=allow_unreg)
    if type(memberOrSV).__name__ == "FakePlayer":  # can't use isinstance, circular import
        return memberOrSV
    else:
        userdata = User()
        userdata.height = memberOrSV
        if nickname is None:
            nickname = f"a {userdata.height:,.3mu} tall person"
        userdata.nickname = nickname
        return userdata


class FakePlayer(User):
    """Generates a fake User based on a dumb string with complex syntax no one will use but me."""
    KEYMAP = AliasMap({
        "nickname": ("nick", "name"),
        "height": (),
        "baseheight": (),
        "baseweight": (),
        "footlength": ("foot", "basefoot"),
        "shoesize": ("shoe", "baseshoe"),
        "hairlength": ("hair", "basehair"),
        "taillength": ("tail", "basetail"),
        "earheight": ("ear", "baseear"),
        "pawtoggle": ("paw"),
        "furtoggle": ("fur"),
        "liftstrength": ("lift", "carry"),
        "walkperhour": ("walk"),
        "runperhour": ("run"),
        "swimperhour": ("swim"),
        "gender": (),
        "scale": ()
    })

    UNITMAP = {
        "nickname": str,
        "height": SV,
        "baseheight": SV,
        "baseweight": WV,
        "footlength": SV,
        "shoesize": str,
        "hairlength": SV,
        "taillength": SV,
        "earheight": SV,
        "pawtoggle": bool,
        "furtoggle": bool,
        "liftstrength": WV,
        "walkperhour": Rate,
        "runperhour": Rate,
        "swimperhour": Rate,
        "gender": str,
        "scale": str
    }

    @classmethod
    def parse(cls, s: str) -> FakePlayer:
        re_full_string = r"\$(\w+=[^;$]+;?)+"
        match = re.match(re_full_string, s)
        if match is None:
            raise InvalidSizeValue(s, "FakePlayer")

        player = FakePlayer()

        s = s.removeprefix("$")
        for group in s.split(";"):
            re_component = r"(\w+)=([^;$]+);?"
            componentmatch = re.match(re_component, group)
            key = componentmatch.group(1)
            val = componentmatch.group(2)
            if key not in cls.KEYMAP:
                raise InvalidStat(key)

            collapsed_key = cls.KEYMAP[key]
            unit = cls.UNITMAP[collapsed_key]

            if collapsed_key == "scale":
                player.scale = parse_scale(val)
            elif collapsed_key == "shoesize":
                player.footlength = from_shoe_size(val)
            elif unit == bool:
                setattr(player, collapsed_key, truthy(val))
            elif unit == str:
                setattr(player, collapsed_key, val)
            elif unit in (SV, WV, Rate):
                val = unit.parse(val)
                setattr(player, collapsed_key, val)

        if player.nickname is None:
            player.nickname = f"a {player.height:,.3mu} tall person"

        return player

    @classmethod
    async def convert(cls, ctx: commands.Context[commands.Bot], argument: str) -> FakePlayer:
        return cls.parse(argument)
