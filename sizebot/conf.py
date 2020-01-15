from pathlib import Path

import appdirs
import toml

from sizebot import utils

# ASCII art
banner = (
    r"   _____ _         ____        _   ____   _____ ""\n"
    r"  / ____(_)       |  _ \      | | |___ \ | ____|""\n"
    r" | (___  _ _______| |_) | ___ | |_  __) || |__  ""\n"
    r"  \___ \| |_  / _ \  _ < / _ \| __||__ < |___ \ ""\n"
    r"  ____) | |/ /  __/ |_) | (_) | |_ ___) | ___) |""\n"
    r" |_____/|_/___\___|____/ \___/ \__|____(_)____/ ""\n"
    r"                                                ")
description = (
    "SizeBot3 is a complete rewrite of SizeBot for the Macropolis and, later, Size Matters server.\n"
    "SizeBot3AndAHalf is a refactorization for SB3 and adds various features.\n"
    "Written by DigiDuncan.\n"
    "The SizeBot Team: DigiDuncan, Natalie, Kelly, AWK_, Benyovski, Arceus3521, Surge The Raichu.")
# Version
# Release versions: major.minor.revision
winkpath = None
userdbpath = None
telemetrypath = None
changespath = None
prefix = None
authtoken = None
admins = None
ids = None
emoji = None
logchannelid = None


class Config:
    __slots__ = ["banner", "description", "version", "winkpath", "userdbpath", "telemetrypath", "changespath", "prefix", "prefix", "authtoken", "admins", "ids", "emoji", "logchannelid"]

    def __init__(self, configDict):
        # File paths
        datadir = getDataDir()
        self.winkpath = datadir / "winkcount.txt"
        self.userdbpath = datadir / "users"
        self.telemetrypath = datadir / "telemetry.json"
        self.changespath = datadir / "changes.json"

        # Sizebot
        self.prefix = utils.getPath(configDict, "sizebot.prefix", "&")

        # Discord
        self.authtoken = utils.getPath(configDict, "discord.authtoken", None)
        self.admins = utils.getPath(configDict, "discord.admins", [])     # List of admins
        self.ids = configDict.get("ids", dict())        # List of ids by name
        self.emoji = configDict.get("emoji", dict())    # List of emojis by name

        self.logchannelid = utils.getPath(configDict, "discord.logchannelid", None)
        if self.logchannelid is not None:
            self.logchannelid = int(self.logchannelid)

    def getId(self, name):
        return self.ids.get(name, 000000000000000000)

    @classmethod
    def load(cls):
        datadir = getDataDir()
        confpath = datadir / "sizebot.conf"

        configDict = toml.load(confpath)

        return Config(configDict)


def getDataDir():
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


conf = Config.load()
