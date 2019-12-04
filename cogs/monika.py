import discord
from discord.ext import commands
from globalsb import *
import digiformatter as df

monikalines = open("text/monikalines.txt").readlines()


# Easter egg
class MonikaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.id == getID("SizeBot"):
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
