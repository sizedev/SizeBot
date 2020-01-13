from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.checks import requireAdmin


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command()
    @commands.check(requireAdmin)
    async def stop(self, ctx):
        await ctx.send("Stopping SizeBot")
        ctx.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
