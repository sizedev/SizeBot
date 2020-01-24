import random
import importlib.resources as pkg_resources
import logging

from discord.ext import commands

import sizebot.data

logger = logging.getLogger("sizebot")

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
        logger.warn("Monika detected.")
        if random.randrange(6) == 1:
            logger.warn("Monika triggered.")
            line = random.choice(monikalines)
            await m.channel.send(line, delete_after = 7)


def setup(bot):
    bot.add_cog(MonikaCog(bot))
