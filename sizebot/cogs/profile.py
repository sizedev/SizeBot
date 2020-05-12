from discord.ext import commands


class ProfileCog(commands.Cog):
    """Profile commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["setpic"],
        usage = "<url>",
        category = "profile"
    )
    async def setpicture(self, ctx, *, url):
        pass

    @commands.command(
        aliases = ["setdesc"],
        usage = "<description...>",
        category = "profile"
    )
    async def setdescription(self, ctx, *, desc):
        pass

    @commands.command(
        aliases = ["clearpic", "unsetpic", "resetpic", "clearpicture", "unsetpicture"],
        category = "profile"
    )
    async def resetpicture(self, ctx):
        pass

    @commands.command(
        aliases = ["cleardesc", "unsetdesc", "resetdesc", "cleardescription", "unsetdescription"],
        category = "profile"
    )
    async def resetdescription(self, ctx):
        pass

    @commands.command(
        usage = "[user]",
        category = "profile"
    )
    async def profile(self, ctx, member = None):
        pass


def setup(bot):
    bot.add_cog(ProfileCog(bot))
