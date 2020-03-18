import logging
import itertools
import discord

from discord.ext import tasks, commands

from sizebot.lib.utils import formatTraceback

colorgen = itertools.cycle([
    discord.Color(0xff0000),  # red
    discord.Color(0xff7700),  # orange
    discord.Color(0xffff00),  # yellow
    discord.Color(0x00ff00),  # green
    discord.Color(0x00ffff),  # cyan
    discord.Color(0x0000ff),  # blue
    discord.Color(0xff00ff)   # purple
])

logger = logging.getLogger("sizebot")


class RainbowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rainbower.start()

    def cog_unload(self):
        self.rainbower.cancel()

    @tasks.loop(seconds=1.0)
    async def rainbower(self):
        try:
            for guild in self.bot.guilds:
                for role in guild.roles:
                    if role.name.lower() == "rainbow":
                        await role.edit(color = next(colorgen))
        except Exception as err:
            logger.error(formatTraceback(err))

    @rainbower.before_loop
    async def before_rainbower(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(RainbowCog(bot))
