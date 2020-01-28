import time
import json
import logging

from sizebot import conf
from sizebot.lib.decimal import Decimal

logger = logging.getLogger("sizebot")


_activeNannies = {}


class Nanny:
    def __init__(self, userid, guildid, endtime):
        self.userid = userid
        self.guildid = guildid
        self.endtime = Decimal(endtime)

    async def check(self, bot):
        if time.time() < self.endtime:
            return True
        guild = await bot.fetch_guild(self.guildid)
        member = await guild.fetch_member(self.userid)
        await member.move_to(None, reason="Naptime!")
        # member = bot.get_guild(self.guildid).get_member(self.memberid)
        # TODO: Kick user from their voice channel
        return False

    def toJson(self):
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "endtime": str(self.endtime),
        }


def start(userid, guildid, durationTV):
    """Start a new naptime nanny"""
    endtime = Decimal(time.time()) + durationTV
    nanny = Nanny(userid, guildid, endtime)
    _activate(nanny)


def stop(userid):
    """Stop a waiting naptime nanny"""
    nanny = _deactivate(userid)
    return nanny


async def check(bot):
    """Have the nannies check their watches"""
    global _activeNannies
    runningNannies = {}
    for userid, nanny in _activeNannies.items():
        try:
            running = await nanny.check(bot)
            if running:
                runningNannies[userid] = nanny
        except Exception as e:
            logger.error(e)
    _activeNannies = runningNannies
    saveToFile()


def _activate(nanny):
    """Activate a new naptime nanny"""
    _activeNannies[nanny.userid] = nanny
    saveToFile()


def _deactivate(userid):
    """Deactivate a waiting naptime nanny"""
    nanny = _activeNannies.pop(userid, None)
    saveToFile()
    return nanny


def loadFromFile():
    """Load all naptime nannies from file"""
    try:
        with open(conf.naptimepath, "r") as f:
            nanniesJson = json.load(f)
    except FileNotFoundError:
        nanniesJson = []
    for nannyJson in nanniesJson:
        nanny = Nanny(**nannyJson)
        _activate(nanny)


def saveToFile():
    """Save all naptime nannies to a file"""
    nanniesJson = [n.toJson() for n in _activeNannies.values()]
    with open(conf.naptimepath, "w") as f:
        json.dump(nanniesJson, f)


def formatSummary():
    return "\n".join(str(n) for n in _activeNannies.values())
