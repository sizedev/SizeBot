from pathlib import Path

import appdirs


def getDataDir():
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


# File paths
datadir = getDataDir()
winkpath = datadir / "winkcount.txt"
guilddbpath = datadir / "guilds"
telemetrypath = datadir / "telemetry.json"
commandfreqpath = datadir / "commandsrun.json"
thispath = datadir / "thistracker.json"
changespath = datadir / "changes.json"
naptimepath = datadir / "naptime.json"
edgepath = datadir / "edgeusers.ini"
confpath = datadir / "sizebot.conf"
