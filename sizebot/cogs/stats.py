
import typing
from decimal import InvalidOperation

import discord
from discord.ext import commands

from sizebot import digilogger as logger
# TODO: Fix this...
from sizebot import userdb
from sizebot.digiSV import SV
from sizebot import digisize
from sizebot.checks import guildOnly


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(guildOnly)
    async def stats(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None):
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        stats = digisize.PersonStats(userdata)
        embedtosend = stats.toEmbed()
        embedtosend.description = f"Sent by *{ctx.message.author.nick}*"
        await ctx.send(embed = embedtosend)

        await logger.info(f"Stats for {memberOrHeight} sent.")

    @commands.command()
    @commands.check(guildOnly)
    async def compare(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.", delete_after = 5)
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = digisize.PersonComparison(userdata1, userdata2)
        await ctx.send(embed = comparison.toEmbed())

        await logger.info(f"Compared {userdata1} and {userdata2}")

    @stats.error
    async def stats_handler(self, ctx, error):
        # TODO: Track down what line is causing this
        if isinstance(error, InvalidOperation):
            await ctx.send(
                "SizeBot cannot perform this action due to a math error.\n"
                f"Are you too big, {ctx.message.author.id}?")
        else:
            raise error


def getUserdata(memberOrSV, nickname = "Raw"):
    if isinstance(memberOrSV, discord.Member):
        userdata = userdb.load(memberOrSV.id)
    else:
        userdata = userdb.User()
        userdata.nickname = nickname
        userdata.height = memberOrSV
    return userdata


# Necessary
def setup(bot):
    bot.add_cog(StatsCog(bot))
