from __future__ import annotations
from pathlib import Path
from typing import Any

import json

from sizebot.lib import errors, paths
from sizebot.lib.units import SV


class Guild:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id", "small_edge", "large_edge", "_high_limit", "_low_limit"]

    def __init__(self, id: int):
        self.id = id
        self.small_edge: int | None = None
        self.large_edge: int | None = None
        self._high_limit: SV | None = None
        self._low_limit: SV | None = None

    @property
    def high_limit(self) -> SV | None:
        return self._high_limit

    @high_limit.setter
    def high_limit(self, value: SV | None):
        if value is not None:
            value = SV(max(0, SV(value)))
        self._high_limit = value

    @property
    def low_limit(self) -> SV | None:
        return self._low_limit

    @low_limit.setter
    def low_limit(self, value: SV | None):
        if value is not None:
            value = SV(max(0, SV(value)))
        self._low_limit = value

    def __str__(self) -> str:
        return (f"<Guild ID = {self.id!r}, "
                f"SMALL_EDGE = {self.small_edge!r}, LARGE_EDGE = {self.large_edge!r}, "
                f"LOW_LIMIT = {self.low_limit!r}, HIGH_LIMIT = {self.high_limit!r}>")

    def __repr__(self) -> str:
        return str(self)

    # Return an python dictionary for json exporting
    def toJSON(self) -> Any:
        return {
            "id":         self.id,
            "small_edge": None if self.small_edge is None else self.small_edge,
            "large_edge": None if self.large_edge is None else self.large_edge,
            "high_limit": None if self.high_limit is None else str(self.high_limit),
            "low_limit":  None if self.low_limit is None else str(self.low_limit)
        }

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata: Any) -> Guild:
        guilddata = Guild(jsondata["id"])
        guilddata.small_edge = jsondata.get("small_edge")
        guilddata.large_edge = jsondata.get("large_edge")
        guilddata.high_limit = jsondata.get("high_limit")
        guilddata.low_limit = jsondata.get("low_limit")
        return guilddata


def get_guild_path(guildid: int) -> Path:
    return paths.guilddbpath / f"{guildid}"


def get_guild_data_path(guildid: int) -> Path:
    return get_guild_path(guildid) / "guild.json"


def save(guilddata: Guild):
    guildid = guilddata.id
    if guildid is None:
        raise errors.CannotSaveWithoutIDException
    path = get_guild_data_path(guildid)
    path.parent.mkdir(exist_ok = True, parents = True)
    jsondata = guilddata.toJSON()
    with open(path, "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(guildid: int) -> Guild:
    path = get_guild_data_path(guildid)
    try:
        with open(path, "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.GuildNotFoundException(guildid)

    guild = Guild.fromJSON(jsondata)

    return guild


def load_or_create(guildid: int) -> Guild:
    try:
        guilddata = load(guildid)
    except errors.GuildNotFoundException:
        guilddata = Guild(guildid)
    return guilddata


def delete(guildid: int):
    path = get_guild_path(guildid)
    path.unlink(missing_ok = True)


def exists(guildid: int) -> bool:
    exists = True
    try:
        load(guildid)
    except errors.GuildNotFoundException:
        exists = False
    return exists
