import io
import random

from discord.ext import commands

import digiformatter as df
import iddb

monikalines = io.open("text/monikalines.txt", encoding="utf-8").readlines()


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
            await m.channel.send(line, delete_after=7)


# Necessary.
def setup(bot):
    bot.add_cog(MonikaCog(bot))
