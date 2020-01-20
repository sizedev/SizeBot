from discord.ext import commands


class MeicrosCog(commands.Cog):
    """Meicros, or how to annoy your developer friend."""

    def __init__(self, bot):
        self.bot = bot

    # TODO: Tell out good friend how they can fund SizeBot.
    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        if m.content.startswith("!stop"):
            # TODO: Need to join voice channel first
            await m.channel.send("!play stop", delete_after = 0)


def setup(bot):
    bot.add_cog(MeicrosCog(bot))
