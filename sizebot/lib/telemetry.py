from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sizebot.lib.units import SV

from dataclasses import dataclass, asdict
from pathlib import Path
import json

import arrow

from sizebot import __version__
from sizebot.lib import paths


class ExistingDateException(Exception):
    pass


class TelemetryMessage:
    def save(self):
        data = self.toJSON()
        if "date" in data:
            raise ExistingDateException
        data["date"] = arrow.now().timestamp()
        data["version"] = __version__
        stringified = json.dumps(data)
        paths.telemetrypath.mkdir(exist_ok = True)
        filepath = paths.telemetrypath / self.filename
        with filepath.open("a") as f:
            f.write(stringified + "\n")

    def toJSON(self):
        return asdict(self)


@dataclass
class CommandRun(TelemetryMessage):
    name: str
    filename = Path("command_run.ndjson")


@dataclass
class ObjectUsed(TelemetryMessage):
    name: str
    filename = Path("object_used.ndjson")


@dataclass
class SizeViewed(TelemetryMessage):
    size: SV
    filename = Path("size_viewed.ndjson")

    def toJSON(self):
        return {"size": str(self.size)}


@dataclass
class RegisterStarted(TelemetryMessage):
    guildid: int
    userid: int
    filename = Path("register_started.ndjson")

    def toJSON(self):
        return {
            "guildid": str(self.guildid),
            "userid": str(self.userid)
        }


@dataclass
class AdvancedRegisterUsed(TelemetryMessage):
    guildid: int
    userid: int
    filename = Path("advanced_register_used.ndjson")

    def toJSON(self):
        return {
            "guildid": str(self.guildid),
            "userid": str(self.userid)
        }


@dataclass
class ProfileCopied(TelemetryMessage):
    guildid: int
    userid: int
    filename = Path("profile_copied.ndjson")

    def toJSON(self):
        return {
            "guildid": str(self.guildid),
            "userid": str(self.userid)
        }


@dataclass
class RegisterStepCompleted(TelemetryMessage):
    guildid: int
    userid: int
    command: str
    completed: bool = False
    filename = Path("register_step_completed.ndjson")

    def toJSON(self):
        return {
            "guildid": str(self.guildid),
            "userid": str(self.userid),
            "command": self.command,
            "completed": self.completed
        }


@dataclass
class Unregistered(TelemetryMessage):
    guildid: int
    userid: int
    filename = Path("register_completed.ndjson")

    def toJSON(self):
        return {
            "guildid": str(self.guildid),
            "userid": str(self.userid)
        }


@dataclass
class ErrorThrown(TelemetryMessage):
    command: str
    error_name: str
    filename = Path("error_thrown.ndjson")


@dataclass
class RateLimit(TelemetryMessage):
    name: str
    filename = Path("rate_limit.ndjson")


@dataclass
class AdminCommand(TelemetryMessage):
    userid: str
    command: str
    filename = Path("admin_command.ndjson")


@dataclass
class UnknownCommand(TelemetryMessage):
    name: str
    filename = Path("unknown_command.ndjson")


@dataclass
class UnknownObject(TelemetryMessage):
    name: str
    filename = Path("unknown_object.ndjson")
