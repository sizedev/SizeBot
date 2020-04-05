import logging
from copy import copy

import discord
from discord.ext import commands

from sizebot.discordplus import commandsplus

logger = logging.getLogger("sizebot")


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def stop(self, ctx):
        """RIP SizeBot."""
        logger.critical(f"Help, {ctx.author.display_name} is closing me!")
        await ctx.send("Stopping SizeBot. ☠️")
        await ctx.bot.close()

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def sudo(self, ctx, victim: discord.Member, *, command):
        """Take control."""
        logger.warn(f"{ctx.author.display_name} made {victim.display_name} run {command}.")
        new_message = copy(ctx.message)
        new_message.author = victim
        new_message.content = ctx.prefix + command
        await self.bot.process_commands(new_message)


def setup(bot):
    bot.add_cog(AdminCog(bot))
