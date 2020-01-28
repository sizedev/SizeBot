from copy import copy

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def stop(self, ctx):
        """RIP SizeBot."""
        await ctx.send("Stopping SizeBot. ☠️")
        await ctx.bot.close()

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def sudo(self, ctx, victim: discord.Member, *, command):
        """Take control."""
        new_message = copy(ctx.message)
        new_message.author = victim
        new_message.content = ctx.prefix + command
        await self.bot.process_commands(new_message)


def setup(bot):
    bot.add_cog(AdminCog(bot))
