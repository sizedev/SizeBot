import typing
from decimal import InvalidOperation

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
# TODO: Fix this...
from sizebot import userdb
from sizebot.digiSV import SV
from sizebot import digisize
from sizebot.checks import guildOnly
from sizebot.digidecimal import toFraction, Decimal


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command()
    @commands.check(guildOnly)
    async def stats(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None):
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        stats = digisize.PersonStats(userdata)
        embedtosend = stats.toEmbed()
        if ctx.message.author.id != userdata.id:
            embedtosend.description = f"Requested by *{ctx.message.author.display_name}*"
        await ctx.send(embed = embedtosend)

        await logger.info(f"Stats for {memberOrHeight} sent.")

    @commandsplus.command()
    @commands.check(guildOnly)
    async def statstxt(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None):
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        stats = digisize.PersonStats(userdata)
        await ctx.send(str(stats))

        await logger.info(f"Stats for {memberOrHeight} sent.")

    @commandsplus.command()
    @commands.check(guildOnly)
    async def compare(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = digisize.PersonComparison(userdata1, userdata2)
        embedtosend = comparison.toEmbed()
        embedtosend.description = f"Requested by *{ctx.message.author.display_name}*"
        await ctx.send(embed = embedtosend)

        await logger.info(f"Compared {userdata1} and {userdata2}")

    @commandsplus.command()
    @commands.check(guildOnly)
    async def comparetxt(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = digisize.PersonComparison(userdata1, userdata2)
        await ctx.send(str(comparison))

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

    @commandsplus.command()
    @commands.check(guildOnly)
    async def objcompare(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        goodheight = userdata.height.toGoodUnit('o', accuracy=2, preferName=True)
        tmp = goodheight.split()
        tmp[0] = toFraction(Decimal(tmp[0]), 4)
        goodheightout = " ".join(tmp)

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or **{goodheightout}**.")
        await logger.info(f"Sent object comparison for {userdata.nickname}.")


def getUserdata(memberOrSV, nickname = "Raw"):
    if isinstance(memberOrSV, discord.Member):
        userdata = userdb.load(memberOrSV.id)
    else:
        userdata = userdb.User()
        userdata.nickname = nickname
        userdata.height = memberOrSV
    return userdata


def setup(bot):
    bot.add_cog(StatsCog(bot))
