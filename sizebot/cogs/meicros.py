from discord.ext import commands


class MeicrosCog(commands.Cog):
    """Meicros, or how to annoy your developer friend."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return

        # !play macros.
        if m.content.startswith("!stop"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play stop", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        elif m.content.startswith("!pause"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play pause", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        elif m.content.startswith("!resume"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play resume", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        elif m.content.startswith("!queue"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play queue", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        elif m.content.startswith("!current"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play current", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        elif m.content.startswith("!volume"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play volume" + m.content[7:], delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()


def setup(bot):
    bot.add_cog(MeicrosCog(bot))
