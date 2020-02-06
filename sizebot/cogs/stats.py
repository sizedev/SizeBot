import typing
import logging

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib import userdb
from sizebot.lib import proportions
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases = ["stat"],
        usage = "[user/height]"
    )
    @commands.guild_only()
    async def stats(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        """User stats command.

        Get tons of user stats about yourself, a user, or a raw height.
        Stats: current height, current weight, base height, base weight,
        foot length, foot width, toe height, pointer finger length, thumb width,
        fingerprint depth, hair width, multiplier.

        Examples:
        `&stats` (defaults to stats about you.)
        `&stats @User`
        `&stats 10ft`
        """
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        stats = proportions.PersonStats(userdata)
        embedtosend = stats.toEmbed()
        if ctx.message.author.id != userdata.id:
            embedtosend.description = f"Requested by *{ctx.message.author.display_name}*"
        await ctx.send(embed = embedtosend)

        logger.info(f"Stats for {memberOrHeight} sent.")

    @commandsplus.command(
        usage = "[user/height]"
    )
    @commands.guild_only()
    async def statstxt(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        """User stats command, raw text version.

        Get tons of user stats about yourself, a user, or a raw height.
        Stats: current height, current weight, base height, base weight,
        foot length, foot width, toe height, pointer finger length, thumb width,
        fingerprint depth, hair width, multiplier.

        Examples:
        `&statstxt` (defaults to stats about you.)
        `&statstxt @User`
        `&statstxt 10ft`
        """
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        stats = proportions.PersonStats(userdata)
        await ctx.send(str(stats))

        logger.info(f"Stats for {memberOrHeight} sent.")

    @commandsplus.command(
        usage = "[user/height] <user/height>"
    )
    @commands.guild_only()
    async def compare(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Compare two users' size."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler.
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        embedtosend = comparison.toEmbed()
        embedtosend.description = f"Requested by *{ctx.message.author.display_name}*"
        await ctx.send(embed = embedtosend)

        logger.info(f"Compared {userdata1} and {userdata2}")

    @commandsplus.command(
        usage = "[user/height] <user/height>"
    )
    @commands.guild_only()
    async def comparetxt(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Compare two users' size, raw text version."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler.
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        await ctx.send(str(comparison))

        logger.info(f"Compared {userdata1} and {userdata2}")

    @commandsplus.command(
        aliases = ["objectcompare", "objcomp"]
    )
    @commands.guild_only()
    async def objcompare(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        """See how tall you are in comparison to an object."""
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        userdata = getUserdata(memberOrHeight)

        goodheight = userdata.height.toGoodUnit('o', preferName=True, spec=".2")
        tmp = goodheight.split()
        tmp[0] = format(Decimal(tmp[0]), "%4&2")
        goodheightout = " ".join(tmp)

        goodweight = userdata.weight.toGoodUnit('o', preferName=True, spec=".2")
        tmp2 = goodweight.split()
        tmp2[0] = format(Decimal(tmp2[0]), "%4&2")
        goodweightout = " ".join(tmp2)

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about **{goodheightout}**. They weigh about **{goodweightout}**.")
        logger.info(f"Sent object comparison for {userdata.nickname}.")

    @commandsplus.command(
        aliases = ["look", "examine"],
        usage = "[object]"
    )
    @commands.guild_only()
    async def lookat(self, ctx, *, what):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&lookat man`
        `&look book`
        `&examine building`"""
        logger.info(f"{ctx.message.author.display_name} looked at {what}.")

        if what not in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            await ctx.send(f"Sorry, *{what}* is not a valid object.")
            return

        userdata = getUserdata(ctx.message.author)
        userstats = proportions.PersonStats(userdata)
        userheight = userstats.avgheightcomp
        compdata = getUserdata(userheight)

        stats = proportions.PersonStats(compdata)
        embedtosend = stats.toEmbed()
        if ctx.message.author.id != userdata.id:
            embedtosend.description = f"Reverse stats for {userdata.nickname}*\n*Requested by *{ctx.message.author.display_name}*"
        await ctx.send(embed = embedtosend)


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
