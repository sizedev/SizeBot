from pathlib import Path

import appdirs
import toml

from sizebot import utils


def getDataDir():
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


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
winkpath = None
userdbpath = None
telemetrypath = None
changespath = None
prefix = "&"
authtoken = None
admins = []             # List of admins
ids = dict()            # List of ids by name
emoji = dict()          # List of emojis by name
logchannelid = None

# File paths
datadir = getDataDir()
winkpath = datadir / "winkcount.txt"
userdbpath = datadir / "users"
telemetrypath = datadir / "telemetry.json"
changespath = datadir / "changes.json"
confpath = datadir / "sizebot.conf"


def load():
    global prefix, authtoken, admins, ids, emoji, logchannelid
    configDict = toml.load(confpath)

    # Sizebot
    if utils.hasPath(configDict, "sizebot.prefix"):
        prefix = utils.getPath(configDict, "sizebot.prefix")

    # Discord
    if utils.hasPath(configDict, "discord.authtoken"):
        authtoken = utils.getPath(configDict, "discord.authtoken")
    if utils.hasPath(configDict, "discord.admins"):
        admins = utils.getPath(configDict, "discord.admins")
    if "ids" in configDict:
        ids = configDict["ids"]
    if "emoji" in configDict:
        emoji = configDict["emoji"]

    logchannelid = utils.getPath(configDict, "discord.logchannelid")
    if logchannelid is not None:
        logchannelid = int(logchannelid)


def getId(self, name):
    return ids.get(name, 000000000000000000)
