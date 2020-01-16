from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib.checks import requireAdmin


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def stop(self, ctx):
        """RIP SizeBot."""
        await ctx.send("Stopping SizeBot")
        await ctx.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
