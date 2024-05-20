from __future__ import annotations
from collections.abc import Callable
from typing import Literal, Any, TypeVar, cast, get_args

import json
from copy import copy
from functools import total_ordering
import importlib.resources as pkg_resources
from pathlib import Path

import arrow
from arrow.arrow import Arrow

import discord

import sizebot.data
from sizebot.lib import errors, paths
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.gender import Gender
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.unitsystem import UnitSystem
from sizebot.lib.utils import truncate
from sizebot.lib.stats import AVERAGE_HEIGHT, AVERAGE_WEIGHT, PlayerStats

BASICALLY_ZERO = Decimal("1E-27")

modelJSON = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))

MoveTypeStr = Literal["walk", "run", "climb", "crawl", "swim"]
MOVETYPES = get_args(MoveTypeStr)

MemberOrFake = discord.Member | FakePlayer
MemberOrFakeOrSize = MemberOrFake | SV


def str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    return str(v)


@total_ordering
class User:
    # __slots__ declares to python what attributes to expect.
    __slots__ = [
        "guildid", "id", "nickname", "lastactive", "picture_url", "description", "gender", "display",
        "_height", "baseheight", "baseweight", "footlength", "pawtoggle", "furtoggle",
        "hairlength", "taillength", "earheight", "liftstrength", "triggers", "unitsystem", "species", "soft_gender",
        "avatar_url", "walkperhour", "runperhour", "swimperhour",
        "currentscalestep", "currentscaletalk", "scaletalklock",
        "currentmovetype", "movestarted", "movestop",
        "registration_steps_remaining", "_macrovision_model", "_macrovision_view",
        "button", "tra_reports", "allowchangefromothers"
    ]

    def __init__(self, guildid: int, id: int, nickname: str):
        self.guildid: int = guildid
        self.id: int = id
        self.nickname: str = nickname
        self.picture_url: str | None = None
        self.description: str | None = None
        self.gender: Gender | None = None
        self.display: bool = True
        self._height: SV = AVERAGE_HEIGHT
        self.baseheight: SV = AVERAGE_HEIGHT
        self.baseweight: WV = AVERAGE_WEIGHT
        self.footlength: SV | None = None
        self.pawtoggle: bool = False
        self.furtoggle: bool = False
        self.hairlength: SV | None = None
        self.taillength: SV | None = None
        self.earheight: SV | None = None
        self.liftstrength: WV | None = None
        self.walkperhour: SV | None = None
        self.runperhour: SV | None = None
        self.swimperhour: SV | None = None
        self.currentscalestep: Diff | None = None
        self.currentscaletalk: Diff | None = None
        self.scaletalklock: bool = False
        self.currentmovetype: MoveTypeStr | None = None
        self.movestarted: Arrow | None = None
        self.movestop: TV | None = None
        self.triggers: dict[str, Diff] = {}
        self.button: Diff | None = None
        self.tra_reports = 0
        self.unitsystem: UnitSystem = "m"
        self.species: str | None = None
        self.soft_gender: str | None = None
        self.avatar_url: str | None = None
        self.lastactive: Arrow | None = None
        self.registration_steps_remaining: list[str] = []
        self._macrovision_model: str | None = None
        self._macrovision_view: str | None = None
        self.allowchangefromothers: bool = False

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
    def footname(self) -> str:
        # TODO: Replace with stats
        return "Paw" if self.pawtoggle else "Foot"

    @property
    def hairname(self) -> str:
        # TODO: Replace with stats
        return "Fur" if self.furtoggle else "Hair"

    @property
    def autogender(self) -> str:
        return self.gender or self.soft_gender or "m"

    @property
    def weight(self) -> WV:
        return WV(self.baseweight * (self.scale ** 3))

    @property
    def viewscale(self) -> Decimal:
        """How scaled up the world looks to this user"""
        return 1 / self.scale

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
    def fromJSON(cls, jsondata: dict[str, Any]) -> User:
        jsondata = migrate_json(jsondata)
        userdata = User(int(jsondata["guildid"]), int(jsondata["id"]), cast(str, jsondata["nickname"]))
        userdata.lastactive = optional_parse(arrow.get, jsondata["lastactive"])
        userdata.picture_url = cast(str, jsondata["picture_url"])
        userdata.description = cast(str, jsondata["description"])
        userdata.gender = cast(Gender | None, jsondata["gender"])
        userdata.display = cast(bool, jsondata["display"])
        userdata.height = SV(jsondata["height"])
        userdata.baseheight = SV(jsondata["baseheight"])
        userdata.baseweight = WV(jsondata["baseweight"])
        userdata.footlength = optional_parse(SV, jsondata["footlength"])
        userdata.pawtoggle = cast(bool, jsondata["pawtoggle"])
        userdata.furtoggle = cast(bool, jsondata["furtoggle"])
        userdata.hairlength = optional_parse(SV, jsondata["hairlength"])
        userdata.taillength = optional_parse(SV, jsondata["taillength"])
        userdata.earheight = optional_parse(SV, jsondata["earheight"])
        userdata.liftstrength = optional_parse(WV, jsondata["liftstrength"])
        userdata.walkperhour = optional_parse(SV, jsondata["walkperhour"])
        userdata.runperhour = optional_parse(SV, jsondata["runperhour"])
        userdata.swimperhour = optional_parse(SV, jsondata["swimperhour"])
        userdata.currentscalestep = optional_parse(Diff.fromJSON, jsondata["currentscalestep"])
        userdata.currentscaletalk = optional_parse(Diff.fromJSON, jsondata["currentscaletalk"])
        userdata.scaletalklock = cast(bool, jsondata["scaletalklock"])
        userdata.currentmovetype = cast(MoveTypeStr | None, jsondata["currentmovetype"])
        userdata.movestarted = optional_parse(arrow.get, jsondata["movestarted"])
        userdata.movestop = optional_parse(TV, jsondata["movestop"])
        userdata.triggers = {k: Diff.fromJSON(v) for k, v in cast(dict[str, str], jsondata["triggers"]).items()}
        userdata.button = optional_parse(Diff.fromJSON, jsondata["button"])
        userdata.tra_reports = cast(int, jsondata["tra_reports"])
        userdata.unitsystem = cast(UnitSystem, jsondata["unitsystem"])
        userdata.species = cast(str, jsondata["species"])
        userdata.registration_steps_remaining = cast(list[str], jsondata["registration_steps_remaining"])
        userdata._macrovision_model = cast(str | None, jsondata["macrovision_model"])
        userdata._macrovision_view = cast(str | None, jsondata["macrovision_view"])
        userdata.allowchangefromothers = cast(bool, jsondata["allowchangefromothers"])
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

    def __truediv__(self, other: Decimal) -> User:
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) / other
        return newuserdata

    def __pow__(self, other: Decimal) -> User:
        newuserdata = copy(self)
        newuserdata.scale = Decimal(self.scale) ** other
        return newuserdata

    @classmethod
    def from_fake(cls, fake: FakePlayer) -> User:
        userdata = User(0, 0, "")
        for k, v in fake.statvalues.items():
            setattr(userdata, k, v)
        return userdata

    @classmethod
    def from_height(cls, height: SV) -> User:
        return User.from_fake(FakePlayer(height=height))


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


def load(guildid: int, userid: int, *, member: discord.Member | None = None, allow_unreg: bool = False) -> User:
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


def load_or_fake(arg: MemberOrFake | SV, *, allow_unreg: bool = False) -> User:
    if isinstance(arg, discord.Member):
        return load(arg.guild.id, arg.id, member=arg, allow_unreg=allow_unreg)
    elif isinstance(arg, FakePlayer):
        return User.from_fake(arg)
    elif isinstance(arg, SV):
        return User.from_height(arg)


def load_or_fake_height(arg: MemberOrFake | SV, *, allow_unreg: bool = False) -> SV:
    if isinstance(arg, discord.Member):
        user = load(arg.guild.id, arg.id, member=arg, allow_unreg=allow_unreg)
        return user.height
    elif isinstance(arg, FakePlayer):
        return User.from_fake(arg).height
    elif isinstance(arg, SV):
        return arg


def load_or_fake_weight(arg: MemberOrFake | WV, *, allow_unreg: bool = False) -> WV:
    if isinstance(arg, discord.Member):
        user = load(arg.guild.id, arg.id, member=arg, allow_unreg=allow_unreg)
        return user.weight
    elif isinstance(arg, FakePlayer):
        return User.from_fake(arg).weight
    elif isinstance(arg, WV):
        return arg


T = TypeVar("T")


def optional_parse(parser: Callable[[str], T], val: str | None) -> T | None:
    if val is None:
        return None
    return parser(val)


def migrate_json(jsondata: dict[str, Any]) -> dict[str, Any]:
    if "allowchangefromothers" not in jsondata:
        jsondata["allowchangefromothers"] = False
    if "tra_reports" not in jsondata:
        jsondata["tra_reports"] = 0
    if "scaletalklock" not in jsondata:
        jsondata["scaletalklock"] = False
    if "movestarted" not in jsondata:
        jsondata["movestarted"] = 0.0
    if "triggers" not in jsondata:
        jsondata["triggers"] = {}
    for settable in ["walkperhour", "runperhour", "swimperhour", "currentscaletalk", "currentscalestep",
                     "currentmovetype", "movestop", "button"]:
        jsondata[settable] = None
    return jsondata
