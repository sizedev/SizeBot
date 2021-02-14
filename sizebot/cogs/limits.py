import logging
from sizebot.lib.errors import GuildNotFoundException, UserNotFoundException

import discord
from discord.ext import commands

from sizebot.lib import guilddb, proportions, userdb, nickmanager
from sizebot.lib.checks import is_mod
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


async def on_message(m):
    # non-guild messages
    if not isinstance(m.author, discord.Member):
        return

    try:
        userdata = userdb.load(m.guild.id, m.author.id)
    except UserNotFoundException:
        return
    try:
        guilddata = guilddb.load(m.guild.id)
    except GuildNotFoundException:
        return

    if guilddata.low_limit:
        if userdata.height < guilddata.low_limit:
            userdata.height = guilddata.low_limit
            userdb.save(userdata)

    if guilddata.high_limit:
        if userdata.height > guilddata.high_limit:
            userdata.height = guilddata.high_limit
            userdb.save(userdata)

    if userdata.display:
        await nickmanager.nickUpdate(m.author)


class EdgeCog(commands.Cog):
    """Commands to create or clear edge users."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        category = "misc"
    )
    async def limits(self, ctx):
        """See the guild's current caps."""
        guilddata = guilddb.loadOrCreate(ctx.guild.id)
        await ctx.send(f"**SERVER-SET LOW CAPS AND HIGH CAPS:**\nLow Limit: {'*Unset*' if guilddata.low_limit is None else guilddata.low_limit}\nHigh Limit: {'*Unset*' if guilddata.high_limit is None else guilddata.high_limit}")

    @commands.command(
        aliases = ["lowlimit", "lowcap", "setlowcap", "setfloor"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def setlowlimit(self, ctx, *, size: SV):
        """Set the low size limit (floor)."""
        guilddata = guilddb.loadOrCreate(ctx.guild.id)
        guilddata.low_limit = size
        guilddb.save(guilddata)
        await ctx.send(f"{size:,.3mu} is now the lowest allowed size in this guild.")
        logger.info(f"{size:,.3mu} is now the low size cap in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["highlimit", "highcap", "sethighcap", "setceiling"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def sethighlimit(self, ctx, *, size: SV):
        """Set the high size limit (ceiling)."""
        guilddata = guilddb.loadOrCreate(ctx.guild.id)
        guilddata.high_limit = size
        guilddb.save(guilddata)
        await ctx.send(f"{size:,.3mu} is now the highest allowed size in this guild.")
        logger.info(f"{size:,.3mu} is now the high size cap in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resetlowlimit", "resetlowcap", "clearlowcap", "resetfloor", "clearfloor"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def clearlowlimit(self, ctx):
        """Set the low size limit (floor)."""
        guilddata = guilddb.loadOrCreate(ctx.guild.id)
        guilddata.low_limit = None
        guilddb.save(guilddata)
        await ctx.send("There is now no lowest allowed size in this guild.")
        logger.info(f"Cleared low size cap in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resethighlimit", "resethighcap", "clearhighcap", "resetceiling", "clearceiling"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def clearhighlimit(self, ctx):
        """Set the high size limit (ceiling)."""
        guilddata = guilddb.loadOrCreate(ctx.guild.id)
        guilddata.high_limit = None
        guilddb.save(guilddata)
        await ctx.send("There is now no highest allowed size in this guild.")
        logger.info(f"Cleared high size cap in guild {ctx.guild.id}.")


def setup(bot):
    bot.add_cog(EdgeCog(bot))
