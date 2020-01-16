import json

from sizebot import conf


class Telemetry():
    def __init__(self, unknowns=None, commands=None, ratelimits=None):
        self.unknowns = unknowns or {}
        self.commands = commands or {}
        self.ratelimits = ratelimits or {}

    def incrementUnknown(self, name):
        count = self.unknowns.get(name, 0)
        self.unknowns[name] = count + 1

    def incrementCommand(self, name):
        count = self.commands.get(name, 0)
        self.commands[name] = count + 1

    def incrementRateLimit(self, name):
        count = self.ratelimits.get(name, 0)
        self.ratelimits[name] = count + 1

    def save(self):
        conf.telemetrypath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(conf.telemetrypath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    def toJSON(self):
        """Return a python dictionary for json exporting"""
        return {
            "unknowns": self.unknowns,
            "commands": self.commands,
            "ratelimits": self.ratelimits
        }

    @classmethod
    def load(cls):
        try:
            with open(conf.telemetrypath, "r") as f:
                jsondata = json.load(f)
        except FileNotFoundError:
            return Telemetry()
        return Telemetry.fromJSON(jsondata)

    @classmethod
    def fromJSON(cls, jsondata):
        unknowns = jsondata["unknowns"]
        commands = jsondata["commands"]
        ratelimits = jsondata["ratelimits"]
        return Telemetry(unknowns, commands, ratelimits)
