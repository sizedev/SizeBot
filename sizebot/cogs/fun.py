import asyncio

from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.conf import conf

tasks = {}


class FunCog(commands.Cog):
    """Commands for non-size stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def repeat(self, ctx, delay: float, *, message: str):
        if ctx.message.author.id != conf.getId("DigiDuncan"):
            return
        await ctx.message.delete(delay=0)

        async def repeatTask():
            while True:
                await ctx.send(message)
                await asyncio.sleep(delay * 60)
        task = self.bot.loop.create_task(repeatTask())
        tasks[ctx.message.author.id] = task

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def stoprepeat(self, ctx):
        await ctx.message.delete(delay=0)
        tasks[ctx.message.author.id].cancel()
        del tasks[ctx.message.author.id]

    @commandsplus.command(
        hidden = True
    )
    async def say(self, ctx, *, message: str):
        await ctx.message.delete(delay=0)
        if ctx.message.author.id == conf.getId("DigiDuncan"):
            await ctx.send(message)

    @commandsplus.command(
        usage = "<message>"
    )
    async def sing(self, ctx, *, s: str):
        await ctx.message.delete(delay=0)
        newstring = f":musical_score: *{s}* :musical_note:"
        await ctx.send(newstring)


def setup(bot):
    bot.add_cog(FunCog(bot))
