from __future__ import annotations
from typing import Any
from collections.abc import Callable

import toml

from sizebot.lib import paths
from sizebot.lib.attrdict import AttrDict
from sizebot.lib.pathdict import get_by_path, set_by_path


SENTINEL = object()


class ConfigError(Exception):
    pass


class ConfigField:
    def __init__(self,
                 var: str,
                 path: str,
                 *,
                 type: Callable[[Any], Any] = lambda v: v,
                 default: Any = SENTINEL,
                 initdefault: Any = SENTINEL):
        self.var = var
        self.path = path
        self.default = default
        self.initdefault = initdefault
        self.type = type

    def load(self, config: Config, configDict: dict):
        if self.default is not SENTINEL:
            val = get_by_path(configDict, self.path, SENTINEL)
            if val is SENTINEL:
                val = self.default
            else:
                val = self.type(val)
            config[self.var] = val
        else:
            config[self.var] = get_by_path(configDict, self.path)

    def init(self, configDict: dict):
        if self.initdefault is not SENTINEL:
            set_by_path(configDict, self.path, self.initdefault)


class Config(AttrDict):
    def __init__(self, fields: list[ConfigField]):
        super().__init__()
        # This avoids an infinite recursion issue with __getattr__()
        self._fields: list[ConfigField]
        super(AttrDict, self).__setattr__("_fields", fields)

    def load(self):
        try:
            configDict = toml.load(paths.confpath)
        except FileNotFoundError as e:
            raise ConfigError(f"Configuration file not found: {e.filename}")

        try:
            for f in self._fields:
                f.load(self, configDict)
        except KeyError as e:
            raise ConfigError(f"Required configuration field not found: {e.path}")

    def init(self):
        if paths.confpath.exists():
            raise FileExistsError(f"Configuration file already exists: {paths.confpath}")
        paths.confpath.parent.mkdir(parents=True, exist_ok=True)

        configDict = {}
        for f in self._fields:
            f.init(configDict)
        with open(paths.confpath, "w") as f:
            toml.dump(configDict, f)


conf = Config([
    ConfigField("prefix", "sizebot.prefix", default="&"),
    ConfigField("name", "sizebot.name", default="SizeBot"),
    ConfigField("environment", "sizebot.environment", default="production"),
    ConfigField("activity", "sizebot.activity", default="Ratchet and Clank: Size Matters"),
    ConfigField("authtoken", "discord.authtoken", initdefault="INSERT_BOT_TOKEN_HERE"),
    ConfigField("logchannelid", "discord.logchannelid", type=int, default=None),
    ConfigField("bugwebhookurl", "discord.bugwebhookurl", default=None)
])
