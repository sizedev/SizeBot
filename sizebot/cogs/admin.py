import logging
from copy import copy

import discord
from discord.ext import commands

from sizebot.lib import userdb

logger = logging.getLogger("sizebot")


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["hcf"],
        hidden = True
    )
    @commands.is_owner()
    async def halt(self, ctx):
        """RIP SizeBot."""
        logger.critical(f"Help, {ctx.author.display_name} is closing me!")
        await ctx.send("Stopping SizeBot. ☠️")
        await ctx.bot.close()

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def dump(self, ctx, *, user: discord.Member = None):
        """RIP SizeBot."""
        if user is None:
            user = ctx.author
        userdata = userdb.load(ctx.guild.id, user.id)
        await ctx.send(f"```{repr(userdata)}```")

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def sudo(self, ctx, victim: discord.Member, *, command):
        """Take control."""
        logger.warn(f"{ctx.author.display_name} made {victim.display_name} run {command}.")
        new_message = copy(ctx.message)
        new_message.author = victim
        if new_message.content.startswith(ctx.prefix):
            new_message.content = command
        else:
            new_message.content = ctx.prefix + command
        await self.bot.process_commands(new_message)


def setup(bot):
    bot.add_cog(AdminCog(bot))
