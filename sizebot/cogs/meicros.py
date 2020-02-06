from discord.ext import commands
from sizebot import conf

chocola = 161027274764713984


def isACommand(commands, message):
    for command in commands:
        if message.startswith(conf.prefix + command):
            return True
    if message.startswith("!stop"):
        return True
    return False


class MeicrosCog(commands.Cog):
    """Meicros, or how to annoy your developer friend."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        # Emulate what a good stop command would be.
        if m.content.startswith("!stop"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play stop", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        if m.content.startswith("!queue"):
            channel = m.author.voice.channel
            await channel.connect()
            await m.channel.send("!play queue", delete_after = 0)
            leave = m.guild.voice_client
            await leave.disconnect()
        # Tell our good friend how they can fund SizeBot.
        if m.author.id == chocola and isACommand(self.bot.all_commands.keys(), m.content) and not m.content.endswith("--no-fund"):
            await m.channel.send(f"1 packages are looking funding.\nRun `{conf.prefix}fund` for details.\n(To stop seeing this message, run commands with `--no-fund`.)")


def setup(bot):
    bot.add_cog(MeicrosCog(bot))
