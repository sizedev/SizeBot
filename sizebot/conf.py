import toml

from sizebot.lib import paths
from sizebot.lib.pathdict import PathDict

# ASCII art
banner = (
    r"   _____ _         ____        _   ____   _____ ""\n"
    r"  / ____(_)       |  _ \      | | |___ \ | ____|""\n"
    r" | (___  _ _______| |_) | ___ | |_  __) || |__  ""\n"
    r"  \___ \| |_  / _ \  _ < / _ \| __||__ < |___ \ ""\n"
    r"  ____) | |/ /  __/ |_) | (_) | |_ ___) | ___) |""\n"
    r" |_____/|_/___\___|____/ \___/ \__|____(_)____/ ""\n"
    r"                                                ")

prefix = "&"
name = "SizeBot"
activity = "Ratchet and Clank: Size Matters"
authtoken = None
logchannelid = None


def load():
    global prefix, name, activity, authtoken, logchannelid
    configDict = PathDict(toml.load(paths.confpath))

    # SizeBot
    prefix = configDict.get("sizebot.prefix", prefix)
    name = configDict.get("sizebot.name", name)
    activity = configDict.get("sizebot.activity", activity)

    # Discord
    authtoken = configDict.get("discord.authtoken", authtoken)

    logchannelid = configDict.get("discord.logchannelid", logchannelid)
    if logchannelid is not None:
        logchannelid = int(logchannelid)
