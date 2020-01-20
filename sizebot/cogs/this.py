from discord.ext import commands


def findLatestNonThis(messages):
    for message in messages:
        if not message.content.startswith("^") or message.content.lower() == "this":
            return message


class ThisCog(commands.Cog):
    """This Points!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        if m.content.startswith("^") or m.content.lower() == "this":
            channel = m.channel
            messages = await channel.history(limit=100).flatten()
            # Add a "this point" to findLatestNonThis(messages).author in a file
            # that keeps track of this points.


def setup(bot):
    bot.add_cog(ThisCog(bot))
