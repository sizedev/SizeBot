import random

import importlib.resources as pkg_resources

from discord.ext import commands

from sizebot import digiformatter as df
from sizebot import iddb
from sizebot import text

monikalines = pkg_resources.read_text(text, "monikalines.txt")


# Easter egg
class MonikaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.id == iddb.getID("SizeBot"):
            return
        if "monika" not in m.content.lower():
            return
        df.warn("Monika detected.")
        if random.randrange(6) == 1:
            df.warn("Monika triggered.")
            line = random.choice(monikalines)
            await m.channel.send(line, delete_after = 7)


# Necessary.
def setup(bot):
    bot.add_cog(MonikaCog(bot))
