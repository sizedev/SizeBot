import logging

import discord
from discord.ext import commands

from sizebot.lib import userdb, nickmanager
from sizebot.lib.diff import Rate as ParseableRate

logger = logging.getLogger("sizebot")


async def on_message(m):
    # non-guild messages
    if not isinstance(m.author, discord.Member):
        return

    for _, userid in userdb.listUsers(guildid = m.guild.id):
        userdata = userdb.load(m.guild.id, userid)

        for trigger, diff in userdata.triggers.items():
            if trigger in m.content:
                if diff.changetype == "multiply":
                    userdata.height *= diff.amount
                elif diff.changetype == "add":
                    userdata.height += diff.amount
                elif diff.changetype == "power":
                    userdata = userdata ** diff.amount

        if userdata.display:
            await nickmanager.nick_update(m.author)


class TriggerCog(commands.Cog):
    """Commands to create or clear triggers."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        category = "trigger"
    )
    async def triggers(self, ctx):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        triggers = [f"{trigger}: {diff}" for trigger, diff in userdata.triggers.items()]
        out = "**Triggers**:\n" + "\n".join(triggers)
        await ctx.send(out)

    @commands.command(
        usage = "<trigger> <diff>",
        category = "trigger"
    )
    async def settrigger(self, ctx, trigger, *, diff: ParseableRate):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.triggers[trigger] = diff
        await ctx.send(f"Set trigger word {trigger!r} to scale {diff}.")

    @commands.command(
        usage = "<trigger> <diff>",
        category = "trigger",
        aliases = ["resettrigger", "unsettrigger", "removetrigger"]
    )
    async def cleartrigger(self, ctx, *, trigger):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        del userdata.triggers[trigger]
        await ctx.send(f"Removed trigger word {trigger!r}.")


def setup(bot):
    bot.add_cog(TriggerCog(bot))
