import time
import json
import logging

from sizebot import userdb, conf
from sizebot.lib import proportions
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV, TV

logger = logging.getLogger("sizebot")


_activeChanges = {}


class Change:
    def __init__(self, userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None, startTime=None, lastRan=None):
        self.userid = userid
        self.guildid = guildid
        self.addPerSec = addPerSec and SV(addPerSec)
        self.mulPerSec = mulPerSec and Decimal(mulPerSec)
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
        userdata = userdb.load(self.userid)
        newheight = (userdata.height * mulPerTick) + addPerTick
        if self.stopSV is not None and ((newheight < userdata.height and self.stopSV >= newheight) or (newheight > userdata.height and self.stopSV <= newheight)):
            newheight = self.stopSV
            running = False
        userdata.height = newheight
        userdb.save(userdata)
        guild = bot.get_guild(self.guildid)
        member = guild.get_member(self.userid)
        await proportions.nickUpdate(member)
        return running

    @property
    def endtime(self):
        if self.stopTV is None:
            return None
        return self.startTime + self.stopTV

    def __str__(self):
        return f"gid:{self.guildid}/uid:{self.userid} {self.addPerSec:.3} *{self.mulPerSec} , stop at {self.stopSV}, stop after {self.stopTV}s"

    def toJson(self):
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "addPerSec": self.addPerSec and str(self.addPerSec),
            "mulPerSec": self.mulPerSec and str(self.mulPerSec),
            "stopSV": self.stopSV and str(self.stopSV),
            "stopTV": self.stopTV and str(self.stopTV),
            "startTime": self.startTime and str(self.startTime),
            "lastRan": self.lastRan and str(self.lastRan)
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
    global _activeChanges
    runningChanges = {}
    for key, change in _activeChanges.items():
        try:
            running = await change.apply(bot)
            if running:
                runningChanges[key] = change
        except Exception as e:
            logger.error(e)
    _activeChanges = runningChanges
    saveToFile()


def _activate(change):
    """Activate a new change task"""
    _activeChanges[change.userid, change.guildid] = change
    saveToFile()


def _deactivate(userid, guildid):
    """Deactivate a running change task"""
    change = _activeChanges.pop((userid, guildid), None)
    saveToFile()
    return change


def loadFromFile():
    """Load all change tasks from a file"""
    try:
        with open(conf.changespath, "r") as f:
            changesJson = json.load(f)
    except FileNotFoundError:
        changesJson = []
    for changeJson in changesJson:
        change = Change(**changesJson)
        _activate(change)


def saveToFile():
    """Save all change tasks to a file"""
    changesJson = [c.toJson() for c in _activeChanges.values()]
    with open(conf.changespath, "w") as f:
        json.dump(changesJson, f)


def formatSummary():
    return "\n".join(str(c) for c in _activeChanges.values())
