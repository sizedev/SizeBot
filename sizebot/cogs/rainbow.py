import itertools
import logging

import discord
from discord.ext import commands, tasks

from sizebot.lib.utils import format_traceback

colorgen = itertools.cycle([
    discord.Color.red(),     # red
    discord.Color.orange(),  # orange
    discord.Color.gold(),    # yellow
    discord.Color.green(),   # green
    discord.Color.teal(),    # cyan
    discord.Color.blue(),    # blue
    discord.Color.purple()   # purple
])

logger = logging.getLogger("sizebot")

# According to a member of the Discord API guild, rainbow roles are
# "[...] the one thing that [Discord] has publicly said not to do"
# I did not know this at the time.
# DO NOT USE THIS COG.


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
                        # PERMISSION: requires manage_roles
                        await role.edit(color = next(colorgen))
        except Exception as err:
            logger.error(format_traceback(err))

    @rainbower.before_loop
    async def before_rainbower(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(RainbowCog(bot))
