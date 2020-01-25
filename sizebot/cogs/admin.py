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
        await ctx.send("Stopping SizeBot")
        await ctx.bot.close()


def setup(bot):
    bot.add_cog(AdminCog(bot))
