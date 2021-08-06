from collections import defaultdict
import logging

import discord
from discord.ext import commands
from sizebot.lib.errors import UserNotFoundException

from sizebot.conf import conf
from sizebot.lib import userdb, nickmanager
from sizebot.lib.diff import Diff
from sizebot.lib.versioning import release_on

logger = logging.getLogger("sizebot")

user_triggers = defaultdict(dict)


def set_cached_trigger(guildid, authorid, trigger, diff):
    user_triggers[trigger][guildid, authorid] = diff


def unset_cached_trigger(guildid, authorid, trigger):
    if (guildid, authorid) not in user_triggers[trigger]:
        return
    del user_triggers[trigger][guildid, authorid]
    if not user_triggers[trigger]:
        del user_triggers[trigger]


def set_trigger(guildid, authorid, trigger, diff):
    set_cached_trigger(guildid, authorid, trigger, diff)
    userdata = userdb.load(guildid, authorid)
    userdata.triggers[trigger] = diff
    userdb.save(userdata)


def unset_trigger(guildid, authorid, trigger):
    unset_cached_trigger(guildid, authorid, trigger)
    userdata = userdb.load(guildid, authorid)
    if trigger in userdata.triggers:
        del userdata.triggers[trigger]
        userdb.save(userdata)


class TriggerCog(commands.Cog):
    """Commands to create or clear triggers."""

    def __init__(self, bot):
        self.bot = bot
        for guildid, userid in userdb.listUsers():
            try:
                userdata = userdb.load(guildid, userid)
            except UserNotFoundException:
                continue
            for trigger, diff in userdata.triggers.items():
                user_triggers[trigger][guildid, userid] = diff

    @commands.Cog.listener()
    async def on_message(self, m):
        # non-guild messages
        if not isinstance(m.author, discord.Member):
            return

        if m.author.bot:
            return

        if m.content.startswith(conf.prefix):
            return

        # Collect list of triggered users
        users_to_update = defaultdict(list)
        for keyword, users in user_triggers.items():
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

    @release_on("3.6")
    @commands.command(
        category = "trigger",
        usage = "[user]"
    )
    async def triggers(self, ctx, user: discord.Member):
        if user is None:
            userid = ctx.author.id
        else:
            userid = user.id
        userdata = userdb.load(ctx.guild.id, userid)
        triggers = [f"`{trigger}`: {diff}" for trigger, diff in userdata.triggers.items()]
        out = "**Triggers**:\n" + "\n".join(triggers)
        await ctx.send(out)

    @release_on("3.6")
    @commands.command(
        usage = "<trigger> <diff>",
        category = "trigger"
    )
    async def settrigger(self, ctx, trigger, *, diff: Diff):
        set_trigger(ctx.guild.id, ctx.author.id, trigger, diff)
        await ctx.send(f"Set trigger word {trigger!r} to scale {diff}.")

    @release_on("3.6")
    @commands.command(
        usage = "<trigger>",
        category = "trigger",
        aliases = ["resettrigger", "unsettrigger", "removetrigger"]
    )
    async def cleartrigger(self, ctx, *, trigger):
        unset_trigger(ctx.guild.id, ctx.author.id, trigger)
        await ctx.send(f"Removed trigger word {trigger!r}.")

    @release_on("3.6")
    @commands.command(
        usage = "<trigger>",
        category = "trigger",
        aliases = ["resetalltriggers", "unsetalltriggers", "removealltriggers"]
    )
    async def clearalltriggers(self, ctx, *, trigger):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        for trigger in userdata.triggers.keys():
            unset_trigger(ctx.guild.id, ctx.author.id, trigger)
        await ctx.send("Removed all trigger words.")


def setup(bot):
    bot.add_cog(TriggerCog(bot))
