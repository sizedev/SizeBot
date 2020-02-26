import importlib.resources as pkg_resources
import toml

import sizebot.data

ids = None
emojis = None


class AttrDict:
    def __init__(self, data):
        self.__dict__ = data


def loadids(data):
    global ids
    # Get the ids dictionary (or an empty dict if none exists)
    idsdict = data.get("ids", {})
    # make all names lowercase
    idsdict = {name.lower(): userid for name, userid in idsdict.items()}
    # create the enum
    ids = AttrDict(idsdict)


def loademojis(data):
    global emojis
    # Get the ids dictionary (or an empty dict if none exists)
    emojisdict = data.get("emojis", {})
    # make all names lowercase
    emojisdict = {name.lower(): emoji for name, emoji in emojisdict.items()}
    # create the enum
    emojis = AttrDict(emojisdict)


def load():
    # Load constants toml file
    data = toml.loads(pkg_resources.read_text(sizebot.data, "constants.ini"))
    loadids(data)
    loademojis(data)


load()
