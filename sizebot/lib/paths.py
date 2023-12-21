from pathlib import Path

import appdirs


def get_data_dir():
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


# File paths
datadir = get_data_dir()
winkpath = datadir / "winkcount.txt"
guilddbpath = datadir / "guilds"
telemetrypath = datadir / "telemetry"
thispath = datadir / "thistracker.json"
changespath = datadir / "changes.json"
naptimepath = datadir / "naptime.json"
confpath = datadir / "sizebot.conf"
whitelistpath = datadir / "whitelist.txt"
