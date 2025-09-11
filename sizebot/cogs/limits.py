import logging
from sizebot.lib.errors import GuildNotFoundException, UserNotFoundException

import discord
from discord.ext import commands

from sizebot.lib import guilddb, userdb, nickmanager
from sizebot.lib.checks import is_mod
from sizebot.lib.types import GuildContext
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


class LimitCog(commands.Cog):
    """Commands to create or clear edge users."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["caps", "limit", "cap"]
        category = "misc"
    )
    @commands.guild_only()
    async def limits(self, ctx: GuildContext):
        """See the guild's current caps."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        print_glow = '*Unset*' if guilddata.low_limit is None else format(guilddata.low_limit, ",.3mu")
        print_ghigh = '*Unset*' if guilddata.high_limit is None else format(guilddata.high_limit, ",.3mu")
        print_ulow = '*Unset*' if userdata.minimum_limit is None else format(userdata.minimum_limit, ",.3mu")
        print_uhigh = '*Unset*' if userdata.maximum_limit is None else format(userdata.maximum_limit, ",.3mu")
        await ctx.send(f"**SERVER-SET LOW CAPS AND HIGH CAPS:**\nLow Limit: {print_glow}\nHigh Limit: {print_ghigh}\n**USER-SET LOW CAPS AND HIGH CAPS:**\nLow Limit: {print_ulow}\nHigh Limit: {print_uhigh}")

    @commands.command(
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def setguildminimum(self, ctx: GuildContext, *, size: SV):
        """Set the low size limit (floor)."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.low_limit = size
        guilddb.save(guilddata)
        await ctx.send(f"{size:,.3mu} is now the lowest allowed size in this guild.")
        logger.info(f"{size:,.3mu} is now the low size cap in guild {ctx.guild.id}.")

    @commands.command(
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def setguildmaximum(self, ctx: GuildContext, *, size: SV):
        """Set the high size limit (ceiling)."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.high_limit = size
        guilddb.save(guilddata)
        await ctx.send(f"{size:,.3mu} is now the highest allowed size in this guild.")
        logger.info(f"{size:,.3mu} is now the high size cap in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resetguildminimum"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def clearguildminimum(self, ctx: GuildContext):
        """Set the low size limit (floor)."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.low_limit = None
        guilddb.save(guilddata)
        await ctx.send("There is now no lowest allowed size in this guild.")
        logger.info(f"Cleared low size cap in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resetguildmaximum"],
        usage = "[size]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def clearguildmaximum(self, ctx: GuildContext):
        """Set the high size limit (ceiling)."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.high_limit = None
        guilddb.save(guilddata)
        await ctx.send("There is now no highest allowed size in this guild.")
        logger.info(f"Cleared high size cap in guild {ctx.guild.id}.")

    @commands.command(
        usage = "[size]",
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def setminimum(self, ctx: GuildContext, *, size: SV):
        """Set the low size limit (floor)."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.minimum_limit = size
        userdb.save(userdata)
        await ctx.send(f"{size:,.3mu} is now your minimum size.")
        logger.info(f"{size:,.3mu} is now the low size cap for user {userdata.id}.")

    @commands.command(
        usage = "[size]",
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def setmaximum(self, ctx: GuildContext, *, size: SV):
        """Set the high size limit (ceiling)."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.maximum_limit = size
        userdb.save(userdata)
        await ctx.send(f"{size:,.3mu} is now your maximum size.")
        logger.info(f"{size:,.3mu} is now the high size cap for user {userdata.id}.")

    @commands.command(
        aliases = ["resetminimum"],
        usage = "[size]",
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def clearminimum(self, ctx: GuildContext):
        """Clear the low size limit (floor)."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.minimum_limit = None
        userdb.save(userdata)
        await ctx.send("You no longer have a lower limit.")
        logger.info(f"None is now the low size cap for user {userdata.id}.")

    @commands.command(
        aliases = ["resetmaximum"],
        usage = "[size]",
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def clearmaximum(self, ctx: GuildContext):
        """Set the high size limit (ceiling)."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.maximum_limit = None
        userdb.save(userdata)
        await ctx.send("You no longer have an upper limit.")
        logger.info(f"None is now the high size cap for user {userdata.id}.")

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
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
                await m.channel.send(f"{userdata.nickname} hit the lower limit of this guild and has been set to {guilddata.low_limit:,.3mu}.")

        if guilddata.high_limit:
            if userdata.height > guilddata.high_limit:
                userdata.height = guilddata.high_limit
                userdb.save(userdata)
                await m.channel.send(f"{userdata.nickname} hit the upper limit of this guild and has been set to {guilddata.high_limit:,.3mu}.")

        if userdata.minimum_limit:
            if userdata.height < userdata.minimum_limit:
                userdata.height = userdata.minimum_limit
                userdb.save(userdata)
                await m.channel.send(f"{userdata.nickname} hit their lower limit and has been set to {userdata.minimum_limit:,.3mu}.")

        if userdata.maximum_limit:
            if userdata.height > userdata.maximum_limit:
                userdata.height = userdata.maximum_limit
                userdb.save(userdata)
                await m.channel.send(f"{userdata.nickname} hit their upper limit and has been set to {userdata.maximum_limit:,.3mu}.")

        if userdata.display:
            await nickmanager.nick_update(m.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(LimitCog(bot))
