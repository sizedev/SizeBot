import random

import importlib.resources as pkg_resources

from discord.ext import commands

from sizebot import logger
import sizebot.data

monikalines = pkg_resources.read_text(sizebot.data, "monikalines.txt").splitlines()


class MonikaCog(commands.Cog):
    """Easter egg"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        if "monika" not in m.content.lower():
            return
        await logger.warn("Monika detected.")
        if random.randrange(6) == 1:
            await logger.warn("Monika triggered.")
            line = random.choice(monikalines)
            await m.channel.send(line, delete_after = 7)


def setup(bot):
    bot.add_cog(MonikaCog(bot))
