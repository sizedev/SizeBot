import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split('.'), obj)


# Show an incoming DMs in console
class DmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if not isinstance(m.channel, discord.DMChannel):
            if not isinstance(m.author, discord.Member):
                channelName = getattr(m.channel, "name", None)
                guildId = deepgetattr(m.channel, "guild.id", None)
                embeds = [e.to_dict() for e in m.embeds]
                logger.msg(
                    f"Received a message from {m.author.name}#{m.author.discriminator} that wasn't a DM: {m.content}\n"
                    f"    Channel name: {channelName\n}"
                    f"    Guild ID: {guildId}\n"
                    f"    Channel ID: {m.channel.id}\n"}
                    f"    Channel type: {m.channel.type.name}\n"
                    f"    Message type: {m.type.name}\n"
                    f"    Embeds: {len(m.embeds)}\n{embeds}\n}"
                    f"    Attachments: {len(m.attachments)}\n"
                    f"    System content: {m.system_content}\n"
                    f"    URL: https://discordapp.com/channels/{guildId}/{m.channel.id}/{m.id}"
                )

            return
        logger.msg(f"DM from {m.author.name}#{m.author.discriminator}: {m.content}")


# Necessary.
def setup(bot):
    bot.add_cog(DmCog(bot))
