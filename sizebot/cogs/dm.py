import discord
from discord.ext import commands

from sizebot import digilogger as logger
from sizebot.utils import deepgetattr


async def dump_message(m):
    channelName = getattr(m.channel, "name", None)
    guildId = deepgetattr(m.channel, "guild.id")
    embeds = [e.to_dict() for e in m.embeds]
    if m.author.discriminator == "0000":
        return
    await logger.warn(
        f"Received a message from {m.author.name}#{m.author.discriminator} that wasn't a DM: {m.content}\n"
        f"    URL: {m.jump_url}\n"
        f"    Guild ID: {guildId}\n"
        f"    Channel ID: {m.channel.id}\n"
        f"    Message ID: {m.id}\n"
        f"    Channel name: {channelName}\n"
        f"    Channel type: {m.channel.type.name}\n"
        f"    Message type: {m.type.name}\n"
        f"    Embeds: {len(m.embeds)}\n{embeds}\n"
        f"    Attachments: {len(m.attachments)}\n"
        f"    System content: {m.system_content}\n"
    )


# Show an incoming DMs in console
class DmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if not isinstance(m.channel, discord.DMChannel):
            if not isinstance(m.author, discord.Member):
                await dump_message(m)
            return
        await logger.info(f"DM from {m.author.name}#{m.author.discriminator}: {m.content}")


# Necessary.
def setup(bot):
    bot.add_cog(DmCog(bot))
