from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sizebot.lib.units import SV

from dataclasses import dataclass, asdict
from pathlib import Path
import json

import arrow

from sizebot.lib import paths


class ExistingDateException(Exception):
    pass


class TelemetryMessage:
    def writerow(self):
        data = asdict(self)
        if "date" in data:
            raise ExistingDateException
        data["date"] = arrow.now().timestamp
        stringified = json.dumps(data)
        paths.telemetrypath.mkdir(exist_ok = True)
        filepath = paths.telemetrypath / self.filename
        with filepath.open("a") as f:
            f.write(stringified + "\n")

    @classmethod
    def append(cls, *args):
        cls(*args).writerow()


@dataclass
class CommandRun(TelemetryMessage):
    name: str
    filename = Path("command_run.ndjson")


@dataclass
class ObjectUsed(TelemetryMessage):
    name: str
    filename = Path("object_used.ndjson")


@dataclass
class SizeUsed(TelemetryMessage):
    size: SV
    filename = Path("size_used.ndjson")


@dataclass
class RegisterStarted(TelemetryMessage):
    userid: int
    filename = Path("register_started.ndjson")


@dataclass
class RegisterProgress(TelemetryMessage):
    userid: int
    command: str
    filename = Path("register_progress.ndjson")


@dataclass
class RegisterCompleted(TelemetryMessage):
    userid: int
    command: str
    filename = Path("register_completed.ndjson")


@dataclass
class Unregistered(TelemetryMessage):
    userid: int
    command: str
    filename = Path("register_completed.ndjson")


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
class UnknownCommand(TelemetryMessage):
    name: str
    filename = Path("unknown_command.ndjson")


@dataclass
class UnknownObject(TelemetryMessage):
    name: str
    filename = Path("unknown_object.ndjson")
