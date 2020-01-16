from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.checks import requireAdmin


class KeypadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def keypad(self, ctx):
        """Test keypad command."""
        await ctx.send("This command is not done!")


def setup(bot):
    bot.add_cog(KeypadCog(bot))
