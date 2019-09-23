import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger


# Show an incoming DMs in console
class DmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if not isinstance(m.channel, discord.DMChannel):
            if not isinstance(m.author, discord.Member):
                logger.msg(
                    f"Received a message from {m.author.name}#{m.author.discriminator} that wasn't a DM: {m.content}\n"
                    f"    Channel type: {type(m.channel)}\n"
                    f"    Message type: {m.type.name}\n"
                    f"    Embeds: {len(m.embeds)}\n"
                    f"    Attachments: {len(m.attachments)}\n"
                    f"    System content: {m.system_content}"
                )

            return
        logger.msg(f"DM from {m.author.name}#{m.author.discriminator}: {m.content}")


# Necessary.
def setup(bot):
    bot.add_cog(DmCog(bot))
