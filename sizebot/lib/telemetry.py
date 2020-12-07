import json

import arrow

from sizebot.lib import paths


class Telemetry:
    def __init__(self, unknowns=None, unknownobjects=None, commands=None, ratelimits=None, permissionerrors=None):
        self.unknowns = unknowns or {}
        self.unknownobjects = unknownobjects or {}
        self.commands = commands or {}
        self.ratelimits = ratelimits or {}
        self.permissionerrors = permissionerrors or {}

    def incrementUnknown(self, name):
        count = self.unknowns.get(name, 0)
        self.unknowns[name] = count + 1

    def incrementUnknownObject(self, name):
        count = self.unknownobjects.get(name, 0)
        self.unknownobjects[name] = count + 1

    def incrementCommand(self, name):
        count = self.commands.get(name, 0)
        self.commands[name] = count + 1

    def incrementRateLimit(self, name):
        count = self.ratelimits.get(name, 0)
        self.ratelimits[name] = count + 1

    def incrementPermissionError(self, name):
        count = self.permissionerrors.get(name, 0)
        self.permissionerrors[name] = count + 1

    def save(self):
        paths.telemetrypath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(paths.telemetrypath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    def toJSON(self):
        """Return a python dictionary for json exporting"""
        return {
            "unknowns": self.unknowns,
            "unknownobjects": self.unknownobjects,
            "commands": self.commands,
            "ratelimits": self.ratelimits,
            "permissionerrors": self.permissionerrors
        }

    @classmethod
    def load(cls):
        try:
            with open(paths.telemetrypath, "r") as f:
                jsondata = json.load(f)
        except FileNotFoundError:
            return Telemetry()
        return Telemetry.fromJSON(jsondata)

    @classmethod
    def fromJSON(cls, jsondata):
        return Telemetry(**jsondata)
        

class CommandFreq:
    def __init__(self, text: str = None):
        self.text = text

    def add(self, command: str, args: str):
        timestamp = arrow.now().timestamp
        output = f"{{\"command\": \"{command}\", \"args\": \"{args}\", \"time\": {timestamp}}}"
        self.text += "\n" + output

    def save(self):
        paths.telemetrypath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(paths.telemetrypath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    @classmethod
    def load(cls):
        try:
            with open(paths.commandfreqpath, "r") as f:
                data = f.read()
        except FileNotFoundError:
            return CommandFreq()
        return CommandFreq(data)
