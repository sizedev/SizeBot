import logging
from copy import copy

import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.types import BotContext

logger = logging.getLogger("sizebot")


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["hcf"],
        hidden = True
    )
    @commands.is_owner()
    async def halt(self, ctx: BotContext):
        """RIP SizeBot."""
        logger.critical(f"Help, {ctx.author.display_name} is closing me!")
        await ctx.send("Stopping SizeBot. ☠️")
        await ctx.bot.close()

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def dump(self, ctx: BotContext, *, user: discord.Member | None = None):
        """Dump a user's data."""
        if user is None:
            user = ctx.author
        userdata = userdb.load(ctx.guild.id, user.id)
        await ctx.send(f"```{repr(userdata)}```")

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def sudo(self, ctx: BotContext, victim: discord.Member, *, command: str):
        """Take control."""
        logger.warn(f"{ctx.author.display_name} made {victim.display_name} run {command}.")
        new_message = copy(ctx.message)
        new_message.author = victim
        if not command.startswith(ctx.prefix):
            command = ctx.prefix + command
        new_message.content = command
        await self.bot.process_commands(new_message)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
