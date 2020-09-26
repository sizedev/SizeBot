import json
from copy import copy
from functools import total_ordering

from sizebot import conf
from sizebot.lib import errors


@total_ordering
class Guild:
    # __slots__ declares to python what attributes to expect.
    __slots__ = ["id"]

    def __init__(self):
        self.id = None

    # Return an python dictionary for json exporting
    def toJSON(self):
        return {}

    # Create a new object from a python dictionary imported using json
    @classmethod
    def fromJSON(cls, jsondata):
        guilddata = Guild()
        return guilddata


def getGuildPath(guildid):
    return conf.guilddbpath / f"{guildid}"


def getGuildDataPath(guildid):
    return getGuildPath(guildid) / f"guild.json"


def save(guilddata):
    guildid = guilddata.id
    if guildid is None:
        raise errors.CannotSaveWithoutIDException
    path = getGuildDataPath(guildid)
    path.parent.mkdir(exist_ok = True, parents = True)
    jsondata = guilddata.toJSON()
    with open(path, "w") as f:
        json.dump(jsondata, f, indent = 4)


def load(guildid):
    path = getGuildDataPath(guildid)
    try:
        with open(path, "r") as f:
            jsondata = json.load(f)
    except FileNotFoundError:
        raise errors.GuildNotFoundException(guildid)

    guild = Guild.fromJSON(jsondata)

    return guild
