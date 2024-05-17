import importlib.resources as pkg_resources
import logging

import discord
from discord import File
from discord.ext import commands

import sizebot.data
from sizebot.lib import userdb
from sizebot.lib.constants import ids
from sizebot.lib.loglevels import EGG
from sizebot.lib.types import BotContext

tasks = {}

logger = logging.getLogger("sizebot")


class FunCog(commands.Cog):
    """Commands for non-size stuff."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def sbsay(self, ctx: BotContext, *, message: str):
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)
        await ctx.send(message)

    @commands.command(
        aliases = ["tra"],
        category = "fun"
    )
    async def report(self, ctx: BotContext, *, user: discord.User):
        """Report a user to the Tiny Rights Alliance."""
        ud = userdb.load(ctx.guild.id, user.id)
        ud.tra_reports += 1
        userdb.save(ud)
        await ctx.send(f"{ud.nickname} has been reported to the Tiny Rights Alliance. This is report **#{ud.tra_reports}**.")

    @commands.command(
        usage = "<message>",
        category = "fun",
        multiline = True
    )
    async def sing(self, ctx: BotContext, *, s: str):
        """Make SizeBot sing a message!"""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)
        newstring = f":musical_score: *{s}* :musical_note:"
        await ctx.send(newstring)

    @commands.command(
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def digipee(self, ctx: BotContext):
        logger.log(EGG, f"{ctx.author.display_name} thinks Digi needs to pee.")
        with pkg_resources.open_binary(sizebot.data, "digipee.mp3") as f:
            # PERMISSION: requires attach_file
            await ctx.send(f"<@{ids.digiduncan}> also has to pee.", file = File(f, "digipee.mp3"))

    @commands.command(
        hidden = True
    )
    async def gamemode(self, ctx: BotContext, *, mode: str):
        logger.log(EGG, f"{ctx.author.display_name} set their gamemode to {mode}.")
        await ctx.send(f"Set own gamemode to `{mode.title()} Mode`")

    @commands.command(
        aliases = ["egg"],
        hidden = True
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def easteregg(self, ctx: BotContext):
        logger.log(EGG, f"{ctx.author.display_name} thought it was that easy, huh.")
        await ctx.send("No.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith("!digipee"):
            cont = await self.bot.get_context(message)
            await cont.invoke(self.bot.get_command("digipee"))


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
