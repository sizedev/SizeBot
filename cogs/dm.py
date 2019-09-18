import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger


# Commands for non-size stuff.
#
# Commands:
class DmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if not isinstance(m.channel, discord.DMChannel):
            return
        logger.msg(f"DM from {m.author.name}#{m.author.discriminator}: {m.content}")


# Necessary.
def setup(bot):
    bot.add_cog(DmCog(bot))
