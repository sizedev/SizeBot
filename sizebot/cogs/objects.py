import logging
import typing

import discord
from discord.ext import commands
from discord.ext.commands.converter import MemberConverter

from sizebot.lib import proportions, telemetry, userdb
from sizebot.lib.loglevels import EGG
from sizebot.lib.objs import DigiObject
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import getUserdata
from sizebot.lib.utils import glitch_string, parseMany


logger = logging.getLogger("sizebot")


class ObjectsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["objcompare", "objcomp"],
        usage = "<object/user> [as user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def objectcompare(self, ctx, *, args: str):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&objectcompare lego`
        `&objcompare moon as @Kelly`
        """

        argslist = args.rsplit(" as ", 1)
        if len(argslist) == 1:
            what = argslist[0]
            who = None
        else:
            what = argslist[0]
            who = argslist[1]

        mc = MemberConverter()

        what = await parseMany(ctx, what, [DigiObject, mc, SV])
        who = await parseMany(ctx, who, [mc, SV])

        if who is None:
            what = await parseMany(ctx, args, [DigiObject, mc, SV])
            who = ctx.author

        if isinstance(who, SV):
            telemetry.SizeViewed(who).save()

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        if isinstance(what, DigiObject):
            oc = what.relativestatsembed(userdata)
            await ctx.send(embed = oc)
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make one sided)
            compdata = getUserdata(what)
        elif isinstance(what, str) and what in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userstats.avgheightcomp
            compdata = getUserdata(compheight)
        else:
            telemetry.UnknownObject(str(what)).save()
            await ctx.send(f"`{what}` is not a valid object, member, or height.")
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = await stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["look", "examine"],
        usage = "<object>",
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

        if isinstance(what, SV):
            telemetry.SizeViewed(what).save()

        userdata = getUserdata(ctx.author)

        if userdata.incomprehensible:
            await ctx.send(glitch_string("hey now, you're an all star, get your game on, go play"))
            return

        if isinstance(what, str):
            what = what.lower()

        if isinstance(what, DigiObject):
            telemetry.ObjectUsed(str(what)).save()
            la = what.relativestatssentence(userdata)
            # Easter eggs.
            if what.name == "photograph":
                la += "\n\n<https://www.youtube.com/watch?v=BB0DU4DoPP4>"
                logger.log(EGG, f"{ctx.author.display_name} is jamming to Nickleback.")
            if what.name == "enderman":
                la += f"\n\n`{ctx.author.display_name} was slain by an Enderman.`"
                logger.log(EGG, f"{ctx.author.display_name} was slain by an Enderman.")
            await ctx.send(la)
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make a sentence)
            compdata = getUserdata(what)
        elif isinstance(what, str) and what.lower() in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userdb.defaultheight
            compdata = getUserdata(compheight, nickname = "an average person")
        elif isinstance(what, str) and what.lower() in ["chocolate", "stuffed animal", "stuffed beaver", "beaver"]:
            logger.log(EGG, f"{ctx.author.display_name} found Chocolate!")
            compdata = getUserdata(SV.parse("11in"), nickname = "Chocolate [Stuffed Beaver]")
            compdata.baseweight = WV.parse("4.8oz")
            compdata.footlength = SV.parse("2.75in")
            compdata.taillength = SV.parse("12cm")
        elif isinstance(what, str) and what.lower() in ["me", "myself"]:
            compdata = userdb.load(ctx.guild.id, ctx.author.id)
        else:
            # Easter eggs.
            if what.lower() in ["all those chickens", "chickens"]:
                await ctx.send("https://www.youtube.com/watch?v=NsLKQTh-Bqo")
                logger.log(EGG, f"{ctx.author.display_name} looked at all those chickens.")
                return
            if what.lower() == "that horse":
                await ctx.send("https://www.youtube.com/watch?v=Uz4bW2yOLXA")
                logger.log(EGG, f"{ctx.author.display_name} looked at that horse (it may in fact be a moth.)")
                return
            if what.lower() == "my horse":
                await ctx.send("https://www.youtube.com/watch?v=o7cCJqya7wc")
                logger.log(EGG, f"{ctx.author.display_name} looked at my horse (my horse is amazing.)")
                return
            if what.lower() == "cake":
                await ctx.send("The cake is a lie.")
                logger.log(EGG, f"{ctx.author.display_name} realized the cake was lie.")
                return
            if what.lower() == "snout":
                await ctx.send("https://www.youtube.com/watch?v=k2mFvwDTTt0")
                logger.log(EGG, f"{ctx.author.display_name} took a closer look at that snout.")
                return
            await ctx.send(
                f"Sorry, I don't know what `{what}` is.\n"
                f"If this is an object or alias you'd like added to SizeBot, "
                f"use `{ctx.prefix}suggestobject` to suggest it "
                f"(see `{ctx.prefix}help suggestobject` for instructions on doing that.)"
            )
            telemetry.UnknownObject(str(what)).save()
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = await stats.toSimpleEmbed(requesterID = ctx.message.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["objectstats"],
        usage = "<object>",
        category = "stats"
    )
    async def objstats(self, ctx, *, what: typing.Union[DigiObject, str]):
        """Get stats about an object.

        Example:
        `&objstats book`"""

        if isinstance(what, str):
            telemetry.UnknownObject(str(what)).save()
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())


def setup(bot):
    bot.add_cog(ObjectsCog(bot))
