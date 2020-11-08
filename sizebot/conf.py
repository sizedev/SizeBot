import toml

from sizebot.lib import paths
from sizebot.lib.attrdict import AttrDict
from sizebot.lib.pathdict import PathDict


SENTINEL = object()


class ConfigError(Exception):
    pass


class ConfigField:
    def __init__(self, var, path, *, type=lambda v: v, default=SENTINEL, initdefault=SENTINEL):
        self.var = var
        self.path = path
        self.default = default
        self.initdefault = initdefault
        self.type = type

    def load(self, config, configDict):
        if self.default is not SENTINEL:
            config[self.var] = self.type(configDict.get(self.path, self.default))
        else:
            config[self.var] = self.type(configDict[self.path])

    def init(self, configDict):
        if self.initdefault is not SENTINEL:
            configDict[self.path] = self.initdefault


class Config(AttrDict):
    def __init__(self, fields):
        self.fields = fields
        super().__init__()

    def load(self):
        try:
            configDict = PathDict(toml.load(paths.confpath))
        except FileNotFoundError as e:
            raise ConfigError(f"Configuration file not found: {e.filename}")

        try:
            for f in self.fields:
                f.load(self, configDict)
        except KeyError as e:
            raise ConfigError(f"Required configuration field not found: {e.path}")

    def init(self):
        if paths.confpath.exists():
            raise FileExistsError(f"Configuration file already exists: {paths.confpath}")
        paths.confpath.parent.mkdir(parents=True, exist_ok=True)

        configDict = PathDict()
        for f in self.fields:
            f.init(configDict)
        with open(paths.confpath, "w") as f:
            toml.dump(configDict.toDict(), f)


conf = Config([
    ConfigField("prefix", "sizebot.prefix", default="&"),
    ConfigField("name", "sizebot.name", default="SizeBot"),
    ConfigField("activity", "sizebot.activity", default="Ratchet and Clank: Size Matters"),
    ConfigField("authtoken", "discord.authtoken", initdefault="INSERT_BOT_TOKEN_HERE"),
    ConfigField("logchannelid", "discord.logchannelid", type=int, default=None)
])
