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

winkpath = None
guilddbpath = None
telemetrypath = None
changespath = None
naptimepath = None
edgepath = None
prefix = "&"
name = "SizeBot"
activity = "Ratchet and Clank: Size Matters"
authtoken = None
logchannelid = None

# File paths
datadir = getDataDir()
winkpath = datadir / "winkcount.txt"
guilddbpath = datadir / "guilds"
telemetrypath = datadir / "telemetry.json"
thispath = datadir / "thistracker.json"
changespath = datadir / "changes.json"
naptimepath = datadir / "naptime.json"
edgepath = datadir / "edgeusers.ini"
confpath = datadir / "sizebot.conf"


def load():
    global prefix, name, activity, authtoken, logchannelid
    configDict = toml.load(confpath)

    # SizeBot
    if utils.hasPath(configDict, "sizebot.prefix"):
        prefix = utils.getPath(configDict, "sizebot.prefix")
    if utils.hasPath(configDict, "sizebot.name"):
        name = utils.getPath(configDict, "sizebot.name")
    if utils.hasPath(configDict, "sizebot.activity"):
        activity = utils.getPath(configDict, "sizebot.activity")

    # Discord
    if utils.hasPath(configDict, "discord.authtoken"):
        authtoken = utils.getPath(configDict, "discord.authtoken")

    logchannelid = utils.getPath(configDict, "discord.logchannelid")
    if logchannelid is not None:
        logchannelid = int(logchannelid)
