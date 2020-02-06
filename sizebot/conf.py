from pathlib import Path

import appdirs
import toml

from sizebot.lib import utils


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
name = "SizeBot"
activity = "Ratchet and Clank: Size Matters"
authtoken = None
admins = []             # List of admins
emoji = dict()          # List of emojis by name
logchannelid = None

# File paths
datadir = getDataDir()
winkpath = datadir / "winkcount.txt"
userdbpath = datadir / "users"
telemetrypath = datadir / "telemetry.json"
thispath = datadir / "thistracker.json"
changespath = datadir / "changes.json"
naptimepath = datadir / "naptime.json"
confpath = datadir / "sizebot.conf"


def load():
    global prefix, name, activity, authtoken, admins, ids, emoji, logchannelid
    configDict = toml.load(confpath)

    # Sizebot
    if utils.hasPath(configDict, "sizebot.prefix"):
        prefix = utils.getPath(configDict, "sizebot.prefix")
    if utils.hasPath(configDict, "sizebot.name"):
        name = utils.getPath(configDict, "sizebot.name")
    if utils.hasPath(configDict, "sizebot.activity"):
        activity = utils.getPath(configDict, "sizebot.activity")

    # Discord
    if utils.hasPath(configDict, "discord.authtoken"):
        authtoken = utils.getPath(configDict, "discord.authtoken")
    if utils.hasPath(configDict, "discord.admins"):
        admins = utils.getPath(configDict, "discord.admins")
    if "emoji" in configDict:
        emoji = configDict["emoji"]

    logchannelid = utils.getPath(configDict, "discord.logchannelid")
    if logchannelid is not None:
        logchannelid = int(logchannelid)


load()
