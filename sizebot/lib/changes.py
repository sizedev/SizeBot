import json
import logging
import time

from sizebot.lib import userdb, paths, nickmanager
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV, TV
from sizebot.lib.utils import pretty_time_delta

logger = logging.getLogger("sizebot")


_active_changes = {}


class Change:
    def __init__(self, userid, guildid, *, addPerSec=0, mulPerSec=1, powPerSec=1, stopSV=None, stopTV=None, startTime=None, lastRan=None):
        self.userid = userid
        self.guildid = guildid
        self.addPerSec = addPerSec and SV(addPerSec)
        self.mulPerSec = mulPerSec and Decimal(mulPerSec)
        self.powPerSec = powPerSec and Decimal(powPerSec)
        self.stopSV = stopSV and SV(stopSV)
        self.stopTV = stopTV and TV(stopTV)
        self.startTime = startTime and Decimal(startTime)
        self.lastRan = lastRan and Decimal(lastRan)

    async def apply(self, bot):
        running = True
        now = Decimal(time.time())
        if self.endtime is not None and self.endtime <= now:
            now = self.endtime
            running = False
        seconds = now - self.lastRan
        self.lastRan = now
        addPerTick = self.addPerSec * seconds
        mulPerTick = self.mulPerSec ** seconds
        powPerTick = self.powPerSec ** seconds
        userdata = userdb.load(self.guildid, self.userid)
        newheight = ((userdata.height ** powPerTick) * mulPerTick) + addPerTick

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
        if newheight <= 0 or newheight == SV.infinity:
            running = False

        # if we're not changing height anymore, cancel the change
        if direction == "none":
            running = False

        userdata.height = newheight
        userdb.save(userdata)
        guild = bot.get_guild(self.guildid)
        member = guild.get_member(self.userid)
        await nickmanager.nick_update(member)
        return running

    @property
    def endtime(self):
        if self.stopTV is None:
            return None
        return self.startTime + self.stopTV

    def __str__(self):
        out = f"G: {self.guildid}| U: {self.userid}\n    "
        out += f"ADD/S: {self.addPerSec:.10}, MUL/S:{self.mulPerSec}"
        if self.stopSV is not None:
            out += f", stop at {self.stopSV}"
        if self.stopTV is not None:
            out += f", stop after {pretty_time_delta(Decimal(self.stopTV))}"
        return out

    def toJSON(self):
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "addPerSec": None if self.addPerSec is None else str(self.addPerSec),
            "mulPerSec": None if self.mulPerSec is None else str(self.mulPerSec),
            "powPerSec": None if self.powPerSec is None else str(self.powPerSec),
            "stopSV": None if self.stopSV is None else str(self.stopSV),
            "stopTV": None if self.stopTV is None else str(self.stopTV),
            "startTime": None if self.startTime is None else str(self.startTime),
            "lastRan": None if self.lastRan is None else str(self.lastRan)
        }


def start(userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None):
    """Start a new change task"""
    startTime = lastRan = time.time()
    change = Change(userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV, startTime=startTime, lastRan=lastRan)
    _activate(change)


def stop(userid, guildid):
    """Stop a running change task"""
    change = _deactivate(userid, guildid)
    return change


async def apply(bot):
    """Apply slow growth changes"""
    global _active_changes
    runningChanges = {}
    for key, change in _active_changes.items():
        try:
            running = await change.apply(bot)
            if running:
                runningChanges[key] = change
        except Exception as e:
            logger.error(e)
    _active_changes = runningChanges
    save_to_file()


def _activate(change):
    """Activate a new change task"""
    _active_changes[change.userid, change.guildid] = change
    save_to_file()


def _deactivate(userid, guildid):
    """Deactivate a running change task"""
    change = _active_changes.pop((userid, guildid), None)
    save_to_file()
    return change


def load_from_file():
    """Load all change tasks from a file"""
    try:
        with open(paths.changespath, "r") as f:
            changesJSON = json.load(f)
    except FileNotFoundError:
        changesJSON = []
    for changeJSON in changesJSON:
        change = Change(**changeJSON)
        _activate(change)


def save_to_file():
    """Save all change tasks to a file"""
    changesJson = [c.toJSON() for c in _active_changes.values()]
    with open(paths.changespath, "w") as f:
        json.dump(changesJson, f)


def format_summary():
    return "\n".join(str(c) for c in _active_changes.values())
