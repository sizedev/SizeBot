import typing
import logging

import discord
from sizebot.discordplus import commands

from sizebot.lib import proportions, userdb
from sizebot.lib.objs import DigiObject
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stats(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None, customName = None):
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
            memberOrHeight = ctx.author

        userdata = getUserdata(memberOrHeight, customName)

        stats = proportions.PersonStats(userdata)

        embedtosend = stats.toEmbed()
        if ctx.author.id != userdata.id:
            embedtosend.description = f"Requested by *{ctx.author.display_name}*"
        await ctx.send(embed = embedtosend)

        logger.info(f"Stats for {memberOrHeight} sent.")

    @commands.command(
        usage = "[user/height]",
        hidden = True,
        category = "stats"
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
            memberOrHeight = ctx.author

        userdata = getUserdata(memberOrHeight)

        stats = proportions.PersonStats(userdata)
        await ctx.send(str(stats))

        logger.info(f"Stats for {memberOrHeight} sent.")

    @commands.command(
        usage = "<stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stat(self, ctx, stat, *, memberOrHeight: typing.Union[discord.Member, SV] = None, customName = None):
        """User stat command.

        Get a single stat about yourself, a user, or a raw height.

        Available stats are: height, weight, foot/feet/shoe, toe, shoeprint/footprint,
        finger/pointer, thumb, nail/fingernail, fingerprint, thread, eye/eyes, hair, tail,
        speed/walk/run, base/baseheight/baseweight, compare/look, scale/multiplier/mult.

        Examples:
        `&stat height` (not specifying a user returns a stat about yourself.)
        `&stats @User weight`
        `&stats 10ft foot`
        """

        statmap = {
            "height":      "height",
            "weight":      "weight",
            "foot":        "foot",
            "feet":        "foot",
            "shoe":        "foot",
            "shoes":       "foot",
            "toe":         "toe",
            "shoeprint":   "shoeprint",
            "footprint":   "shoeprint",
            "finger":      "finger",
            "pointer":     "finger",
            "thumb":       "thumb",
            "nail":        "nail",
            "fingernail":  "fingernail",
            "fingerprint": "fingerprint",
            "thread":      "thread",
            "eye":         "eye",
            "eyes":        "eye",
            "hair":        "hair",
            "tail":        "tail",
            "speed":       "speed",
            "walk":        "speed",
            "run":         "speed",
            "base":        "base",
            "baseheight":  "base",
            "baseweight":  "base",
            "compare":     "compare",
            "look":        "compare",
            "scale":       "scale",
            "multiplier":  "scale",
            "mult":        "scale"
        }

        if memberOrHeight is None:
            memberOrHeight = ctx.author

        userdata = getUserdata(memberOrHeight, customName)

        stats = proportions.PersonStats(userdata)

        logger.info(f"Stat {stat} for {memberOrHeight} sent.")

        if stat not in statmap.keys():
            await ctx.send(f"The `{stat}` stat is not an available option.")
            logger.info(f"Tried to send info on stat {stat}, but that's not a valid stat.")
            return

        stat = statmap[stat]
        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            logger.info(f"Tried to send info on stat {stat}, but this user doesn't have it.")
            return

        await ctx.send(stattosend)

    @commands.command(
        usage = "[user/height] <user/height>",
        category = "stats"
    )
    @commands.guild_only()
    async def compare(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Compare two users' size."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        # TODO: Handle this in an error handler.
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        embedtosend = comparison.toEmbed()
        embedtosend.description = f"Requested by *{ctx.author.display_name}*"
        await ctx.send(embed = embedtosend)

        logger.info(f"Compared {userdata1} and {userdata2}")

    @commands.command(
        usage = "[user/height] <user/height>",
        hidden = True,
        category = "stats"
    )
    @commands.guild_only()
    async def comparetxt(self, ctx, memberOrHeight1: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Compare two users' size, raw text version."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        # TODO: Handle this in an error handler.
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata1 = getUserdata(memberOrHeight1, "Raw 1")
        userdata2 = getUserdata(memberOrHeight2, "Raw 2")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        await ctx.send(str(comparison))

        logger.info(f"Compared {userdata1} and {userdata2}")

    @commands.command(
        aliases = ["natstats", "natstat"],
        category = "stats"
    )
    @commands.guild_only()
    async def naturalstats(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        """See how tall you are in comparison to an object."""
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        userdata = getUserdata(memberOrHeight)

        goodheight = userdata.height.toGoodUnit('o', preferName=True, spec=".2%4&2")
        tmp = goodheight.split()
        tmpout = [tmp[0]] + tmp[3:] + tmp[1:3]  # Move the paranthesis bit of the height string to the end.
        goodheightout = " ".join(tmpout)

        goodweight = userdata.weight.toGoodUnit('o', preferName=True, spec=".2%4&2")
        tmp2 = goodweight.split()
        tmp2out = [tmp2[0]] + tmp2[3:] + tmp2[1:3]  # Move the paranthesis bit of the height string to the end.
        goodweightout = " ".join(tmp2out)

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about **{goodheightout}**. They weigh about **{goodweightout}**.")
        logger.info(f"Sent object comparison for {userdata.nickname}.")

    @commands.command(
        aliases = ["onewaycomp", "owc"],
        usage = "[object/user]",
        category = "stats"
    )
    @commands.guild_only()
    async def onewaycompare(self, ctx, *, what: typing.Union[DigiObject, discord.Member, SV, str], who: typing.Union[discord.Member, SV] = None):  # TODO: Allow a second argument here.
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&lookat man`
        `&look book`
        `&examine building`"""

        if who is None:
            who = ctx.author

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        if isinstance(what, DigiObject):
            oc = what.relativestatsembed(userdata)
            await ctx.send(embed = oc)
            logger.info(f"{ctx.author.display_name} looked at {what.article} {what.name}.")
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make one sided)
            compdata = getUserdata(what, "Raw")
            logger.info(f"{ctx.author.display_name} looked at {what}.")
        elif isinstance(what, str) and what in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userstats.avgheightcomp
            compdata = getUserdata(compheight)
        else:
            await ctx.send(f"`{what}` is not a valid object, member, or height.")
            logger.info(f"{ctx.author.display_name} tried to look at {what}, but that's invalid.")
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = stats.toEmbed()
        if ctx.author.id != userdata.id:  # Future proofing for when you can do owcs for other people.
            embedtosend.description = f"*Requested by *{ctx.author.display_name}*"
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["look", "examine"],
        usage = "[object]",
        category = "stats"
    )
    @commands.guild_only()
    async def lookat(self, ctx, *, what: typing.Union[DigiObject, discord.Member, SV, str]):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&lookat man`
        `&look book`
        `&examine building`"""

        userdata = getUserdata(ctx.author)
        userstats = proportions.PersonStats(userdata)

        if isinstance(what, DigiObject):
            la = what.relativestatssentence(userdata)
            await ctx.send(la)
            logger.info(f"{ctx.author.display_name} looked at {what.article} {what.name}.")
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make a sentence)
            compdata = getUserdata(what, "Raw")
            logger.info(f"{ctx.author.display_name} looked at {what}.")
        elif isinstance(what, str) and what in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userstats.avgheightcomp
            compdata = getUserdata(compheight)
        else:
            await ctx.send(f"`{what}` is not a valid object, member, or height.")
            logger.info(f"{ctx.author.display_name} tried to look at {what}, but that's invalid.")
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = stats.toEmbed()
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["objectstats"],
        usage = "[object]",
        category = "stats"
    )
    async def objstats(self, ctx, *, what: typing.Union[DigiObject, str]):
        """Get stats about an object.

        Example:
        `&objstats book`"""

        if isinstance(what, str):
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())

    @commands.command(
        usage = "[object]",
        hidden = True,
        category = "stats"
    )
    async def objstatstxt(self, ctx, *, what: typing.Union[DigiObject, str]):
        """Get stats about an object. (text version)

        Example:
        `&objstatstxt book`"""

        if isinstance(what, str):
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(what.stats())


def getUserdata(memberOrSV, nickname = "Raw"):
    if nickname is None:
        nickname = "Raw"
    if isinstance(memberOrSV, discord.Member):
        userdata = userdb.load(memberOrSV.guild.id, memberOrSV.id)
    else:
        userdata = userdb.User()
        userdata.nickname = nickname
        userdata.height = memberOrSV
    return userdata


def setup(bot):
    bot.add_cog(StatsCog(bot))
