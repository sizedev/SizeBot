import importlib.resources as pkg_resources

import toml

import sizebot.data
from sizebot.lib.attrdict import AttrDict

ids = None
emojis = None
colors = None


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


def loadcolors(data):
    global colors
    # Get the ids dictionary (or an empty dict if none exists)
    colorsdict = data.get("colors", {})
    # make all names lowercase
    colorsdict = {name.lower(): color for name, color in colorsdict.items()}
    # create the enum
    colors = AttrDict(colorsdict)


def load():
    # Load constants toml file
    data = toml.loads(pkg_resources.read_text(sizebot.data, "constants.ini"))
    loadids(data)
    loademojis(data)
    loadcolors(data)


load()
