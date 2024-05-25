from __future__ import annotations
from queue import Empty, Queue
from typing import Iterator, TypedDict, cast

import json
import logging
import time

from discord.ext import commands

from sizebot.lib import userdb, paths, nickmanager
from sizebot.lib import utils
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, TV
from sizebot.lib.utils import pretty_time_delta

logger = logging.getLogger("sizebot")


def iter_queue[T](q: Queue[T]) -> Iterator[T]:
    while True:
        try:
            yield q.get(False)
        except Empty:
            break


ChangeKey = tuple[int, int]
_active_changes: dict[ChangeKey, Change] = {}
_changes_to_stop: Queue[ChangeKey] = Queue()
_changes_to_start: Queue[Change] = Queue()


class ChangeJSON(TypedDict):
    userid: int
    guildid: int
    addPerSec: str
    mulPerSec: str
    powPerSec: str
    stopSV: str | None
    stopTV: str | None
    startTime: str
    lastRan: str


class Change:
    def __init__(self,
                 userid: int,
                 guildid: int,
                 *,
                 addPerSec: SV = SV(0),
                 mulPerSec: Decimal = Decimal(1),
                 powPerSec: Decimal = Decimal(1),
                 stopSV: SV | None = None,
                 stopTV: TV | None = None,
                 startTime: Decimal,
                 lastRan: Decimal):
        self.userid = userid
        self.guildid = guildid
        self.addPerSec = addPerSec
        self.mulPerSec = mulPerSec
        self.powPerSec = powPerSec
        self.stopSV = stopSV
        self.stopTV = stopTV
        self.startTime = startTime
        self.lastRan = lastRan

    async def apply(self, bot: commands.Bot) -> bool:
        running = True
        now = Decimal(time.time())
        if self.endtime is not None and self.endtime <= now:
            now = self.endtime
            running = False
        seconds = cast(Decimal, now - self.lastRan)
        self.lastRan = now
        addPerTick = cast(SV, self.addPerSec * seconds)
        mulPerTick = cast(Decimal, self.mulPerSec ** seconds)
        powPerTick = cast(Decimal, self.powPerSec ** seconds)
        userdata = userdb.load(self.guildid, self.userid)
        newheight = cast(SV, ((userdata.height ** powPerTick) * mulPerTick) + addPerTick)

        if newheight < userdata.height:
            direction = "down"
        elif newheight > userdata.height:
            direction = "up"
        else:
            direction = "none"

        if (
            self.stopSV is not None
            and (
                (direction == "down" and newheight <= self.stopSV)
                or (direction == "up" and newheight >= self.stopSV)
            )
        ):
            newheight = self.stopSV
            running = False

        # if we've moved past 0 or SV.infinity, cancel the change
        if newheight < SV(0):
            newheight = SV(0)
        if newheight == SV(0) or newheight == SV.infinity:
            running = False

        # if we're not changing height anymore, cancel the change
        if direction == "none":
            running = False

        userdata.height = newheight
        userdb.save(userdata)
        guild = bot.get_guild(self.guildid)
        if guild is None:
            logger.info(f"Unrecognized guild found in Change: guildid={self.guildid} userid={self.userid}")
            return False
        member = guild.get_member(self.userid)
        if member is None:
            logger.info(f"Unrecognized user found in Change: guildid={self.guildid} userid={self.userid}")
            return False
        await nickmanager.nick_update(member)
        return running

    @property
    def endtime(self) -> Decimal | None:
        if self.stopTV is None:
            return None
        return cast(Decimal, self.startTime + self.stopTV)

    def __str__(self) -> str:
        out = f"G: {self.guildid}| U: {self.userid}\n    "
        out += f"ADD/S: {self.addPerSec:.10}, MUL/S:{self.mulPerSec}"
        if self.stopSV is not None:
            out += f", stop at {self.stopSV}"
        if self.stopTV is not None:
            out += f", stop after {pretty_time_delta(Decimal(self.stopTV))}"
        return out

    @classmethod
    def fromJSON(cls, data: ChangeJSON) -> Change:
        return Change(
            data["userid"],
            data["guildid"],
            addPerSec=SV(data["addPerSec"]),
            mulPerSec=Decimal(data["mulPerSec"]),
            powPerSec=Decimal(data["powPerSec"]),
            stopSV=SV(data["stopSV"]) if data["stopSV"] is not None else None,
            stopTV=TV(data["stopTV"]) if data["stopTV"] is not None else None,
            startTime=Decimal(data["startTime"]),
            lastRan=Decimal(data["lastRan"])
        )

    def toJSON(self) -> ChangeJSON:
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "addPerSec": str(self.addPerSec),
            "mulPerSec": str(self.mulPerSec),
            "powPerSec": str(self.powPerSec),
            "stopSV": None if self.stopSV is None else str(self.stopSV),
            "stopTV": None if self.stopTV is None else str(self.stopTV),
            "startTime": str(self.startTime),
            "lastRan": str(self.lastRan)
        }


def start(userid: int, guildid: int, *, addPerSec: SV = SV(0), mulPerSec: Decimal = Decimal(1), stopSV: SV | None = None, stopTV: TV | None = None):
    """Start a new change task"""
    startTime = lastRan = Decimal(time.time())
    change = Change(userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV, startTime=startTime, lastRan=lastRan)
    _changes_to_start.put(change)


def stop(userid: int, guildid: int) -> Change | None:
    """Stop a running change task"""
    key = (userid, guildid)
    _changes_to_stop.put(key)
    return _active_changes.get(key, None)


async def apply(bot: commands.Bot):
    """Apply slow growth changes"""
    global _active_changes
    runningChanges = {}
    for key in iter_queue(_changes_to_stop):
        _active_changes.pop(key, None)
    for change in iter_queue(_changes_to_start):
        _active_changes[change.userid, change.guildid] = change
    for key, change in _active_changes.items():
        try:
            running = await change.apply(bot)
            if running:
                runningChanges[key] = change
        except Exception as e:
            logger.error("Ignoring exception in changes.apply")
            logger.error(utils.format_traceback(e))
    _active_changes = runningChanges
    save_to_file()


def load_from_file():
    """Load all change tasks from a file"""
    try:
        with open(paths.changespath, "r") as f:
            changesJSON: list[ChangeJSON] = json.load(f)
    except FileNotFoundError:
        changesJSON = []
    for changeJSON in changesJSON:
        change = Change.fromJSON(changeJSON)
        _changes_to_start.put(change)


def save_to_file():
    """Save all change tasks to a file"""
    changesJson = [c.toJSON() for c in _active_changes.values()]
    with open(paths.changespath, "w") as f:
        json.dump(changesJson, f)


def format_summary() -> str:
    return "\n".join(str(c) for c in _active_changes.values())
