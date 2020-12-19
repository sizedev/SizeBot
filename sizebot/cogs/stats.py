import logging
import typing

import discord
from discord.ext.commands.converter import MemberConverter
from discord.ext import commands

from sizebot.cogs.register import showNextStep
from sizebot.lib import errors, proportions, userdb, macrovision, telemetry
from sizebot.lib.constants import colors
from sizebot.lib.decimal import Decimal
from sizebot.lib.loglevels import EGG
from sizebot.lib.objs import DigiObject
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.utils import AliasMap, parseMany, prettyTimeDelta, sentence_join

logger = logging.getLogger("sizebot")

statmap = AliasMap({
    "height":           ("size"),
    "weight":           (),
    "foot":             ("feet", "shoe", "shoes", "paw", "paws"),
    "toe":              ("toes"),
    "shoeprint":        ("footprint"),
    "finger":           ("pointer"),
    "thumb":            (),
    "nail":             ("fingernail"),
    "fingerprint":      (),
    "thread":           (),
    "eye":              ("eyes"),
    "hair":             ("fur", "hairlength", "furlength"),
    "hairwidth":        ("furwidth"),
    "tail":             (),
    "ear":              (),
    "speed":            ("walk", "run", "climb", "step", "stride", "pull"),
    "base":             ("baseheight", "baseweight"),
    "compare":          ("look"),
    "scale":            ("multiplier", "mult", "factor"),
    "horizondistance":  ("horizon"),
    "terminalvelocity": ("velocity", "fall"),
    "liftstrength":     ("strength", "lift", "carry", "carrystrength")
})


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stats(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None, *, customName = None):
        """User stats command.

        Get tons of user stats about yourself, a user, or a raw height.

        Examples:
        `&stats` (defaults to stats about you.)
        `&stats @User`
        `&stats 10ft`
        """
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = getUserdata(memberOrHeight, customName, allow_unreg=same_user)

        stats = proportions.PersonStats(userdata)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def basestats(self, ctx, member: discord.Member = None, *, customName = None):
        """User basestats command.

        Get the base stats about yourself or a user.

        Examples:
        `&sbasetats` (defaults to stats about you.)
        `&basestats @User`
        """
        if member is None:
            member = ctx.author

        userdata = userdb.load(ctx.guild.id, member.id)

        stats = proportions.PersonBaseStats(userdata)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statsas(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None,
                      memberOrHeight2: typing.Union[discord.Member, SV] = None, *, customName = None):
        """User stats command with modified bases.

        Get tons of user stats about yourself, a user, or a raw height, as if they were a different height.

        Examples:
        `&statsas 100ft` (defaults to stats about you, if you were a certain height.)
        `&statsas 100ft @User` (get stats about @User if they were a certain height.)
        `&statsas @User @User2` (get stats about @User2 if they were as tall as @User.)
        """
        if memberOrHeight is None:
            raise errors.ArgumentException
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight)

        userdata = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2, customName)
        userdata2.nickname = userdata2.nickname + " as " + userdata.nickname
        userdata2.height = userdata.height

        stats = proportions.PersonStats(userdata2)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        usage = "<stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stat(self, ctx, stat, memberOrHeight: typing.Union[discord.Member, SV] = None, *, customName = None):
        """User stat command.

        Get a single stat about yourself, a user, or a raw height.

        Available stats are: #STATS#

        Examples:
        `&stat height` (not specifying a user returns a stat about yourself.)
        `&stat weight @User`
        `&stat foot 10ft`
        """

        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = getUserdata(memberOrHeight, customName, allow_unreg=same_user)

        stats = proportions.PersonStats(userdata)

        if stat not in statmap.keys():
            await ctx.send(f"The `{stat}` stat is not an available option.")
            return

        try:
            stat = statmap[stat]
        except KeyError:
            await ctx.send(f"`{stat}` is not a stat.")
            return

        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            return

        await ctx.send(stattosend)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statas(self, ctx, stat, memberOrHeight: typing.Union[discord.Member, SV] = None,
                     memberOrHeight2: typing.Union[discord.Member, SV] = None, *, customName = None):
        """User stat command with custom bases.

        Get a single stat about yourself, a user, or a raw height, as if they were a different height.

        Available stats are: #STATS#

        Examples:
        `&statas weight 100ft` (defaults to stats about you, if you were a certain height.)
        `&statas foot 100ft @User` (get stats about @User if they were a certain height.)
        `&statas speed @User @User2` (get stats about @User2 if they were as tall as @User.)
        """

        if memberOrHeight is None:
            raise errors.ArgumentException
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight)

        userdata = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2, customName)
        userdata2.nickname = userdata2.nickname + " as " + userdata.nickname
        userdata2.height = userdata.height

        stats = proportions.PersonStats(userdata2)

        if stat not in statmap.keys():
            await ctx.send(f"The `{stat}` stat is not an available option.")
            return

        try:
            stat = statmap[stat]
        except KeyError:
            await ctx.send(f"`{stat}` is not a stat.")
            return

        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            return

        await ctx.send(stattosend)

    @commands.command(
        aliases = ["comp"],
        usage = "<user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def compare(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Compare two users' size.
        
        If give one user, compares you to that user."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)
        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)

        userdata1 = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2)

        comparison = proportions.PersonComparison(userdata1, userdata2)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["compas"],
        usage = "[user/height] [user/height] <custom name>",
        category = "stats"
    )
    @commands.guild_only()
    async def compareas(self, ctx, asHeight: typing.Union[discord.Member, SV] = None,
                        memberOrHeight: typing.Union[discord.Member, SV] = None, *, customName = None):
        """Compare yourself as a different height and another user."""

        if isinstance(asHeight, SV):
            telemetry.SizeViewed(asHeight)
        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)

        userdata = getUserdata(ctx.message.author)
        asdata = getUserdata(asHeight, customName)
        userdata.height = asdata.height
        userdata.nickname += " as " + asdata.nickname
        comparedata = getUserdata(memberOrHeight)

        comparison = proportions.PersonComparison(userdata, comparedata)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["natstats"],
        category = "stats"
    )
    @commands.guild_only()
    async def lookslike(self, ctx, *, memberOrHeight: typing.Union[discord.Member, SV] = None):
        """See how tall you are in comparison to an object."""
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)

        userdata = getUserdata(memberOrHeight)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about... huh. I can't find them.")
            return

        goodheight = userdata.height.toGoodUnit('o', preferName=True, spec=".2%4&2")
        tmp = goodheight.split()
        tmpout = [tmp[0]] + tmp[3:] + tmp[1:3]  # Move the paranthesis bit of the height string to the end.
        goodheightout = " ".join(tmpout)

        goodweight = userdata.weight.toGoodUnit('o', preferName=True, spec=".2%4&2")
        tmp2 = goodweight.split()
        tmp2out = [tmp2[0]] + tmp2[3:] + tmp2[1:3]  # Move the paranthesis bit of the height string to the end.
        goodweightout = " ".join(tmp2out)

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about **{goodheightout}**. They weigh about **{goodweightout}**.")

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
        `&objectcomapre lego`
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
            telemetry.SizeViewed(who)

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
            telemetry.UnknownObject.append(str(what))
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
            telemetry.SizeViewed(what)

        userdata = getUserdata(ctx.author)

        if isinstance(what, str):
            what = what.lower()

        if isinstance(what, DigiObject):
            telemetry.ObjectUsed.append(str(what))
            la = what.relativestatssentence(userdata)
            # Easter egg.
            if what.name == "photograph":
                la += "\n\n<https://www.youtube.com/watch?v=BB0DU4DoPP4>"
                logger.log(EGG, f"{ctx.author.display_name} is jamming to Nickleback.")
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
            telemetry.UnknownObject.append(str(what))
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = await stats.toEmbed(requesterID = ctx.message.author.id)
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
            telemetry.UnknownObject.append(str(what))
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())

    @commands.command(
        aliases = ["dist", "walk", "run"],
        usage = "<length> [user]",
        category = "stats"
    )
    async def distance(self, ctx, length: typing.Union[SV, TV, str], *, who: typing.Union[discord.Member, SV] = None):
        """How long will it take to walk, run, or climb a distance?

        Example:
        `&distance <length or time>`"""

        if who is None:
            who = ctx.message.author

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} doesn't exist...")
            return

        defaultdata = getUserdata(userdb.defaultheight, "an average person")
        defaultstats = proportions.PersonStats(defaultdata)
        defaultclimblength = Decimal(0.3048)
        defaultclimbspeed = Decimal(4828)
        climblength = Decimal(0.3048) / userdata.viewscale
        climbspeed = Decimal(4828) / userdata.viewscale

        if isinstance(length, str):
            raise errors.InvalidSizeValue(length, "size or time")
        elif isinstance(length, TV):
            walkpersecond = SV(userstats.walkperhour / 3600)
            length = SV(walkpersecond * length)

        defaultwalktimehours = length / defaultstats.walkperhour
        defaultwalksteps = length / defaultstats.walksteplength

        defaultruntimehours = length / defaultstats.runperhour
        defaultrunsteps = length / defaultstats.runsteplength

        defaultclimbtimehours = length / defaultclimbspeed
        defaultclimbsteps = length / defaultclimblength

        newlength = SV(length / userstats.scale)
        walktimehours = length / userstats.walkperhour
        walksteps = length / userstats.walksteplength
        runtimehours = length / userstats.runperhour
        runsteps = length / userstats.runsteplength
        climbtimehours = length / climbspeed
        climbsteps = length / climblength

        walktime = prettyTimeDelta(walktimehours * 60 * 60, roundeventually = True)
        runtime = prettyTimeDelta(runtimehours * 60 * 60, roundeventually = True)
        climbtime = prettyTimeDelta(climbtimehours * 60 * 60, roundeventually = True)

        defaultwalktime = prettyTimeDelta(defaultwalktimehours * 60 * 60, roundeventually = True)
        defaultruntime = prettyTimeDelta(defaultruntimehours * 60 * 60, roundeventually = True)
        defaultclimbtime = prettyTimeDelta(defaultclimbtimehours * 60 * 60, roundeventually = True)

        e = discord.Embed(
            title = f"{length:,.3mu} to {userstats.nickname}",
            description = (
                f"To {userstats.nickname}, {length:,.3mu} would look to be **{newlength:,.3mu}.** "
                f"They could walk that distance in **{walktime}** *({walksteps:,.0f} steps)*, "
                f"run that distance in **{runtime}** *({runsteps:,.0f} strides)*, "
                f"or climb that distance in **{climbtime}** *({climbsteps:,.0f} pulls)*"
            )
        )
        e.set_footer(text = f"An average person could walk {length:,.3mu} in {defaultwalktime} ({defaultwalksteps:,.0f} steps), "
                            f"run that distance in {defaultruntime} ({defaultrunsteps:,.0f} strides), "
                            f"or climb that distance in {defaultclimbtime} ({defaultclimbsteps:,.0f} pulls).")

        await ctx.send(embed = e)

    @commands.command(
        aliases = ["diststats"],
        usage = "<user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def distancestats(self, ctx, memberOrHeight: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Find how long it would take to travel across a person."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2)

        userdata1 = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2)

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["diststat"],
        usage = "<stat> <user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def distancestat(self, ctx, stat, memberOrHeight: typing.Union[discord.Member, SV] = None, *, memberOrHeight2: typing.Union[discord.Member, SV] = None):
        """Find how long it would take to travel across a certain distance on a person.
        
        Available stats are: #STATS#"""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight)
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2)

        userdata1 = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2)

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)

        try:
            embedtosend = comparison.getStatEmbed(statmap[stat])
        except KeyError:
            await ctx.send(f"`{stat}` is not a stat.")
            return

        if embedtosend is None:
            await ctx.send(f"{userdata1.nickname} doesn't have the `{stat}` stat.")
            return

        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = [],
        usage = "<users...>",
        category = "stats"
    )
    @commands.guild_only()
    async def lineup(self, ctx):
        """Lineup a bunch of people for comparison."""

        failedusers = []
        userdatas = []
        for member in ctx.message.mentions:
            try:
                userdatas.append(userdb.load(member.guild.id, member.id, member=member))
            except errors.UserNotFoundException:
                failedusers.append(member)

        # TODO: Raise exception instead
        if failedusers:
            nicks = sentence_join((u.display_name for u in failedusers), oxford=True)
            if len(failedusers) == 1:
                failmessage = f"{nicks} is not a SizeBot user."
            else:
                failmessage = f"{nicks} are not SizeBot users."
            await ctx.send(failmessage)
            return

        users = [{"name": u.nickname, "model": u.macrovision_model, "view": u.macrovision_view, "height": u.height} for u in userdatas]

        nicks = sentence_join((u.nickname for u in userdatas), oxford=True)
        e = discord.Embed(
            title="Click here for lineup image!",
            description=f"Lineup of {nicks}",
            color=colors.cyan,
            url = await macrovision.get_url(users)
        )
        await ctx.send(embed = e)


def getUserdata(memberOrSV, nickname = None, *, allow_unreg=False):
    if isinstance(memberOrSV, discord.Member):
        userdata = userdb.load(memberOrSV.guild.id, memberOrSV.id, member=memberOrSV, allow_unreg=allow_unreg)
    else:
        userdata = userdb.User()
        userdata.height = memberOrSV
        if nickname is None:
            nickname = f"{userdata.height:,.3mu}"
        userdata.nickname = nickname
    return userdata


def setup(bot):
    bot.add_cog(StatsCog(bot))
