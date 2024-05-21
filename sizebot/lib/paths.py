from pathlib import Path

import appdirs


def get_data_dir() -> Path:
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


# File paths
datadir = get_data_dir()
winkpath = datadir / "winkcount.txt"
guilddbpath = datadir / "guilds"
thispath = datadir / "thistracker.json"
changespath = datadir / "changes.json"
confpath = datadir / "sizebot.conf"
blacklistpath = datadir / "blacklist.txt"
