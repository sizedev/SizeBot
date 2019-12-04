import discord
from discord.ext import commands
from globalsb import *


# Commands for non-size stuff.
#
# Commands:
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def repeat(self, ctx, delay: float, *, message: str):
        if ctx.message.author.id != getID("DigiDuncan"): return
        await ctx.message.delete()

        async def repeatTask():
            while True:
                await ctx.send(message)
                await asyncio.sleep(delay * 60)
        task = bot.loop.create_task(repeatTask())
        tasks[ctx.message.author.id] = task

    @commands.command()
    async def stoprepeat(self, ctx):
        await ctx.message.delete()
        tasks[ctx.message.author.id].cancel()
        del tasks[ctx.message.author.id]

    @commands.command()
    async def say(self, ctx, *, message: str):
        await ctx.message.delete()
        if ctx.message.author.id == getID("DigiDuncan"):
            await ctx.send(message)

    @commands.command()
    async def sing(self, ctx, *, string: str):
        await ctx.message.delete()
        newstring = ":musical_score: *" + string + "* :musical_note:"
        await ctx.send(newstring)


# Necessary.
def setup(bot):
    bot.add_cog(FunCog(bot))
