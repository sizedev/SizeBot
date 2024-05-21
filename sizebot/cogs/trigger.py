from typing import Literal

from collections import defaultdict
from dataclasses import dataclass

import discord
from discord.ext import commands

from sizebot.lib.errors import UserNotFoundException
from sizebot.lib.units import SV
from sizebot.conf import conf
from sizebot.lib import userdb, nickmanager
from sizebot.lib.diff import Diff
from sizebot.lib.types import BotContext

_user_triggers = defaultdict(dict)


@dataclass
class Trigger:
    word: str
    changetype: Literal["Diff", "SV"]
    amount: Diff | SV
    private: bool
    samecase: bool
    partial: bool


def _set_cached_trigger(guildid: int, authorid: int, trigger: str, diff: Diff):
    _user_triggers[trigger][guildid, authorid] = diff


def _unset_cached_trigger(guildid: int, authorid: int, trigger: str):
    if (guildid, authorid) not in _user_triggers[trigger]:
        return
    del _user_triggers[trigger][guildid, authorid]
    if not _user_triggers[trigger]:
        del _user_triggers[trigger]


def _set_trigger(guildid: int, authorid: int, trigger: str, diff: Diff):
    userdata = userdb.load(guildid, authorid)
    # Only set the cache _after_ we've check if the user is registered
    _set_cached_trigger(guildid, authorid, trigger, diff)
    userdata.triggers[trigger] = diff
    userdb.save(userdata)


def _unset_trigger(guildid: int, authorid: int, trigger: str):
    _unset_cached_trigger(guildid, authorid, trigger)
    userdata = userdb.load(guildid, authorid)
    if trigger in userdata.triggers:
        del userdata.triggers[trigger]
        userdb.save(userdata)


class TriggerCog(commands.Cog):
    """Commands to create or clear triggers."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        for guildid, userid in userdb.list_users():
            try:
                userdata = userdb.load(guildid, userid)
            except UserNotFoundException:
                continue
            for trigger, diff in userdata.triggers.items():
                _user_triggers[trigger][guildid, userid] = diff

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        # non-guild messages
        if not isinstance(m.author, discord.Member):
            return

        if m.author.bot:
            return

        if m.content.startswith(conf.prefix):
            return

        # Collect list of triggered users
        users_to_update = defaultdict(list)
        for keyword, users in _user_triggers.items():
            if keyword in m.content:
                for (guildid, userid), diff in users.items():
                    # Guild-safe check
                    if guildid == m.guild.id:
                        users_to_update[guildid, userid].append(diff)

        # Update triggered users
        for (guildid, userid), diffs in users_to_update.items():
            userdata = userdb.load(guildid, userid)
            for diff in diffs:
                if diff.changetype == "multiply":
                    userdata.height *= diff.amount
                elif diff.changetype == "add":
                    userdata.height += diff.amount
                elif diff.changetype == "power":
                    userdata = userdata ** diff.amount
            userdb.save(userdata)
            if userdata.display:
                await nickmanager.nick_update(m.guild.get_member(userid))

    @commands.command(
        category = "trigger"
    )
    async def triggers(self, ctx: BotContext):
        """List your trigger words."""
        userid = ctx.author.id
        userdata = userdb.load(ctx.guild.id, userid)
        triggers = [f"`{trigger}`: {diff}" for trigger, diff in userdata.triggers.items()]
        out = "**Triggers**:\n" + "\n".join(triggers)
        await ctx.send(out)

    @commands.command(
        category = "trigger"
    )
    async def exporttriggers(self, ctx: BotContext):
        """Export your trigger words."""
        userid = ctx.author.id
        userdata = userdb.load(ctx.guild.id, userid)
        triggers = [f"&settrigger {trigger} {diff}" for trigger, diff in userdata.triggers.items()]
        out = "```\n" + "\n".join(triggers) + "\n```"
        await ctx.send(out)

    @commands.command(
        usage = "<trigger> <diff>",
        category = "trigger"
    )
    async def settrigger(self, ctx: BotContext, trigger: str, *, diff: Diff):
        """Set a trigger word.

        #ALPHA#
        """
        _set_trigger(ctx.guild.id, ctx.author.id, trigger, diff)
        await ctx.send(f"Set trigger word {trigger!r} to scale {diff}.")

    @commands.command(
        usage = "<trigger>",
        category = "trigger",
        aliases = ["resettrigger", "unsettrigger", "removetrigger"]
    )
    async def cleartrigger(self, ctx: BotContext, *, trigger: str):
        """Remove a trigger word."""
        _unset_trigger(ctx.guild.id, ctx.author.id, trigger)
        await ctx.send(f"Removed trigger word {trigger!r}.")

    @commands.command(
        usage = "<trigger>",
        category = "trigger",
        aliases = ["resetalltriggers", "unsetalltriggers", "removealltriggers"]
    )
    async def clearalltriggers(self, ctx: BotContext):
        """Remove all your trigger words."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        for trigger in userdata.triggers.keys():
            _unset_trigger(ctx.guild.id, ctx.author.id, trigger)
        await ctx.send("Removed all trigger words.")


async def setup(bot: commands.Bot):
    await bot.add_cog(TriggerCog(bot))
