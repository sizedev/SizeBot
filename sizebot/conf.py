from pathlib import Path

import appdirs
import toml

from sizebot import utils
from sizebot import digilogger as logger


class Config:
    __slots__ = ["banner", "description", "version", "winkpath", "userdbpath", "prefix", "prefix", "authtoken", "ids"]

    def __init__(self, configDict):
        # ASCII art
        self.banner = (r". _____ _        ______       _   _____ .""\n"
                       r"./  ___(_)       | ___ \     | | |____ |.""\n"
                       r".\ `--. _ _______| |_/ / ___ | |_    / /.""\n"
                       r". `--. \ |_  / _ \ ___ \/ _ \| __|   \ \.""\n"
                       r"./\__/ / |/ /  __/ |_/ / (_) | |_.___/ /.""\n"
                       r".\____/|_/___\___\____/ \___/ \__\____/ .")

        self.description = ("SizeBot3 is a complete rewrite of SizeBot for the Macropolis and, later, Size Matters server.\n"
                            "SizeBot3AndAHalf is a refactorization for SB3 and adds database support.\n"
                            "Written by DigiDuncan.\n"
                            "The SizeBot Team: DigiDuncan, Natalie, Kelly, AWK_, Benyovski, Arceus3521, Surge The Raichu.")

        # Version
        self.version = "3AAH.0.0.b4"

        # File paths
        datadir = getDataDir()
        self.winkpath = datadir / "winkcount.txt"
        self.userdbpath = datadir / "users"

        # Sizebot
        self.prefix = utils.getPath(configDict, "sizebot.prefix", "&")

        # Discord
        self.authtoken = utils.getPath(configDict, "discord.authtoken", None)
        self.ids = configDict.get("ids", dict())    # List of ids by name

    def getId(self, name):
        return self.ids.get(name, "000000000000000000")

    @classmethod
    def load(cls):
        datadir = getDataDir()
        confpath = datadir / "sizebot.conf"
        logger.info(f"Loading configuration from {confpath}")

        configDict = toml.load(confpath)

        return Config(configDict)


def getDataDir():
    appname = "SizeBot"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


conf = Config.load()
