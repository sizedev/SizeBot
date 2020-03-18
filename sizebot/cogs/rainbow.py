import logging

from discord.ext import tasks, commands

from sizebot.lib.utils import formatTraceback

colorlist = [0xff0000, 0xff7700, 0xffff00, 0x00ff00, 0x00ffff, 0x0000ff, 0xff00ff]

logger = logging.getLogger("sizebot")


class RainbowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.rainbower.start()

    def cog_unload(self):
        self.rainbower.cancel()

    @tasks.loop(seconds=1.0)
    async def rainbower(self):
        try:
            self.index += 1
            if self.index >= len(colorlist):
                self.index = 0
            for guild in self.bot.guilds:
                for role in guild.roles:
                    if role.name.lower() == "rainbow":
                        await role.edit(color = colorlist[self.index])
        except Exception as err:
            logger.error(formatTraceback(err))

    @rainbower.before_loop
    async def before_rainbower(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(RainbowCog(bot))
