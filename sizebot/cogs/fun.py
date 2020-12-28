import asyncio
import importlib.resources as pkg_resources
import logging

from discord import File
from discord.ext import commands

import sizebot.data
from sizebot.lib.constants import ids
from sizebot.lib.loglevels import EGG

tasks = {}

logger = logging.getLogger("sizebot")


class FunCog(commands.Cog):
    """Commands for non-size stuff."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def repeat(self, ctx, delay: float, *, message: str):
        if ctx.author.id != ids.digiduncan:
            return
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        async def repeatTask():
            while True:
                await ctx.send(message)
                await asyncio.sleep(delay * 60)
        task = self.bot.loop.create_task(repeatTask())
        tasks[ctx.author.id] = task

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def stoprepeat(self, ctx):
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)
        tasks[ctx.author.id].cancel()
        del tasks[ctx.author.id]

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def say(self, ctx, *, message: str):
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)
        await ctx.send(message)

    @commands.command(
        usage = "<message>",
        category = "fun",
        multiline = True
    )
    async def sing(self, ctx, *, s: str):
        """Make SizeBot sing a message!"""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)
        newstring = f":musical_score: *{s}* :musical_note:"
        await ctx.send(newstring)

    @commands.command(
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def digipee(self, ctx):
        logger.log(EGG, f"{ctx.author.display_name} thinks Digi needs to pee.")
        with pkg_resources.open_binary(sizebot.data, "digipee.mp3") as f:
            # PERMISSION: requires attach_file
            await ctx.send(f"<@{ids.digiduncan}> also has to pee.", file = File(f, "digipee.mp3"))

    @commands.command(
        hidden = True
    )
    async def gamemode(self, ctx, *, mode):
        logger.log(EGG, f"{ctx.author.display_name} set their gamemode to {mode}.")
        await ctx.send(f"Set own gamemode to `{mode.title()} Mode`")

    @commands.command(
        aliases = ["egg"],
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def easteregg(self, ctx):
        logger.log(EGG, f"{ctx.author.display_name} thought it was that easy, huh.")
        await ctx.send("No.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith("!digipee"):
            cont = await self.bot.get_context(message)
            await cont.invoke(self.bot.get_command("digipee"))


def setup(bot):
    bot.add_cog(FunCog(bot))
