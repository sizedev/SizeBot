import logging

import discord
from discord.ext import commands

from sizebot.lib import userdb, nickmanager
from sizebot.lib.diff import Diff
from sizebot.lib.versioning import release_on

logger = logging.getLogger("sizebot")


class MPCog(commands.Cog):
    """Commands to create or clear triggers."""

    def __init__(self, bot):
        self.bot = bot

    @release_on("3.6")
    @commands.command(
        category = "multiplayer"
    )
    async def pushbutton(self, ctx, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        if userdata.button is None:
            await ctx.send(f"{userdata.nickname} has no button to push!")
            return
        diff = userdata.button
        if diff.changetype == "multiply":
            userdata.height *= diff.amount
        elif diff.changetype == "add":
            userdata.height += diff.amount
        elif diff.changetype == "power":
            userdata = userdata ** diff.amount
        await nickmanager.nick_update(user)
        await ctx.send(f"You pushed {userdata.nickname}'s button! They are now **{userdata.height:,.3mu}** tall.")

    @release_on("3.6")
    @commands.command(
        usage = "<diff>",
        category = "multiplayer"
    )
    async def setbutton(self, ctx, *, diff: Diff):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.button = diff
        userdb.save(userdata)
        await ctx.send(f"Set button to {diff}.")

    @release_on("3.6")
    @commands.command(
        category = "multiplayer",
        aliases = ["resetbutton", "unsetbutton", "removebutton"]
    )
    async def clearbutton(self, ctx,):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.button = None
        userdb.save(userdata)
        await ctx.send("Your button is now disabled.")


def setup(bot):
    bot.add_cog(MPCog(bot))
