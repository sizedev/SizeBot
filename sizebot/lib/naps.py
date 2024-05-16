from __future__ import annotations
from typing import Any

import json
import logging
import time

from discord.ext import commands

from sizebot.lib import paths
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import TV

logger = logging.getLogger("sizebot")


_active_nannies: dict[int, Nanny] = {}


class Nanny:
    def __init__(self, userid: int, guildid: int, endtime: Decimal):
        self.userid = userid
        self.guildid = guildid
        self.endtime = Decimal(endtime)

    async def check(self, bot: commands.Bot) -> bool:
        if time.time() < self.endtime:
            return True
        guild = await bot.fetch_guild(self.guildid)
        # If the bot doesn't have permission to kick users from a voice channel, give up on this nap
        if not guild.me.guild_permissions.move_members:
            return False
        member = await guild.fetch_member(self.userid)
        # PERMISSION: requires move_members
        await member.move_to(None, reason="Naptime!")
        return False

    def toJSON(self) -> Any:
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "endtime": str(self.endtime),
        }


def start(userid: int, guildid: int, durationTV: TV):
    """Start a new naptime nanny"""
    endtime = Decimal(time.time()) + durationTV
    nanny = Nanny(userid, guildid, endtime)
    _activate(nanny)


def stop(userid: int) -> Nanny:
    """Stop a waiting naptime nanny"""
    nanny = _deactivate(userid)
    return nanny


async def check(bot: commands.Bot):
    """Have the nannies check their watches"""
    global _active_nannies
    runningNannies = {}
    for userid, nanny in _active_nannies.items():
        try:
            running = await nanny.check(bot)
            if running:
                runningNannies[userid] = nanny
        except Exception as e:
            logger.error(e)
    _active_nannies = runningNannies
    save_to_file()


def _activate(nanny: Nanny):
    """Activate a new naptime nanny"""
    _active_nannies[nanny.userid] = nanny
    save_to_file()


def _deactivate(userid: int) -> Nanny:
    """Deactivate a waiting naptime nanny"""
    nanny = _active_nannies.pop(userid, None)
    save_to_file()
    return nanny


def load_from_file():
    """Load all naptime nannies from file"""
    try:
        with open(paths.naptimepath, "r") as f:
            nanniesJSON = json.load(f)
    except FileNotFoundError:
        nanniesJSON = []
    for nannyJSON in nanniesJSON:
        nanny = Nanny(**nannyJSON)
        _activate(nanny)


def save_to_file():
    """Save all naptime nannies to a file"""
    nanniesJSON = [n.toJSON() for n in _active_nannies.values()]
    with open(paths.naptimepath, "w") as f:
        json.dump(nanniesJSON, f)


def format_summary() -> str:
    return "\n".join(str(n) for n in _active_nannies.values())
