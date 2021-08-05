import logging
from sizebot.lib.freefall import freefall
from sizebot.lib.versioning import release_on
import typing

import discord
from discord.ext.commands.converter import MemberConverter
from discord.ext import commands

from sizebot.cogs.register import showNextStep
from sizebot.lib import errors, proportions, userdb, macrovision, telemetry
from sizebot.lib.constants import colors, emojis
from sizebot.lib.language import engine
from sizebot.lib.loglevels import EGG
from sizebot.lib.objs import DigiObject
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.utils import AliasMap, glitch_string, parseMany, prettyTimeDelta, sentence_join

logger = logging.getLogger("sizebot")

statmap = AliasMap({
    "height":           ("size"),
    "weight":           ("mass"),
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
    "walk":             ("speed", "step"),
    "run":              (),
    "climb":            ("pull"),
    "crawl":            (),
    "swim":             ("stroke"),
    "jump":             ("jumpheight"),
    "base":             ("baseheight", "baseweight", "basesize"),
    "compare":          ("look"),
    "scale":            ("multiplier", "mult", "factor"),
    "horizondistance":  ("horizon"),
    "terminalvelocity": ("velocity", "fall"),
    "liftstrength":     ("strength", "lift", "carry", "carrystrength"),
    "gender":           (),
    "visibility":       ("visible", "see")
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
            telemetry.SizeViewed(memberOrHeight).save()

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
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2, customName)
        userdata2.nickname = userdata2.nickname + " as " + userdata.nickname
        userdata2.height = userdata.height

        stats = proportions.PersonStats(userdata2)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["get"],
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
            telemetry.SizeViewed(memberOrHeight).save()

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
        aliases = ["getas"],
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
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

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
        aliases = ["comp", "comparison"],
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
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata1 = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2)

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await msg.edit(content = "", embed = embedtosend)

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
            telemetry.SizeViewed(asHeight).save()
        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = getUserdata(ctx.message.author)
        asdata = getUserdata(asHeight, customName)
        userdata.height = asdata.height
        userdata.nickname += " as " + asdata.nickname
        comparedata = getUserdata(memberOrHeight)

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        comparison = proportions.PersonComparison(userdata, comparedata)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await msg.edit(content = "", embed = embedtosend)

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
            telemetry.SizeViewed(memberOrHeight).save()

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
            telemetry.UnknownObject(str(what)).save()
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())

    @commands.command(
        aliases = ["dist", "walk", "run", "climb"],
        usage = "<length> [user]",
        category = "stats"
    )
    async def distance(self, ctx, length: typing.Union[SV, TV, str], *, who: typing.Union[discord.Member, SV] = None):
        """How long will it take to walk, run, climb, etc. a distance/time?

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

        if isinstance(length, str):
            raise errors.InvalidSizeValue(length, "size or time")
        elif isinstance(length, TV):
            walkpersecond = SV(userstats.walkperhour / 3600)
            length = SV(walkpersecond * length)

        defaultwalktimehours = length / defaultstats.walkperhour
        defaultwalksteps = length / defaultstats.walksteplength

        defaultruntimehours = length / defaultstats.runperhour
        defaultrunsteps = length / defaultstats.runsteplength

        defaultclimbtimehours = length / defaultstats.climbperhour
        defaultclimbsteps = length / defaultstats.climbsteplength

        defaultcrawltimehours = length / defaultstats.crawlperhour
        defaultcrawlsteps = length / defaultstats.crawlsteplength

        defaultswimtimehours = length / defaultstats.swimperhour
        defaultswimsteps = length / defaultstats.swimsteplength

        newlength = SV(length / userstats.scale)
        walktimehours = length / userstats.walkperhour
        walksteps = length / userstats.walksteplength
        runtimehours = length / userstats.runperhour
        runsteps = length / userstats.runsteplength
        climbtimehours = length / userstats.climbperhour
        climbsteps = length / userstats.climbsteplength
        crawltimehours = length / userstats.crawlperhour
        crawlsteps = length / userstats.crawlsteplength
        swimtimehours = length / userstats.swimperhour
        swimsteps = length / userstats.swimsteplength

        walktime = prettyTimeDelta(walktimehours * 60 * 60, roundeventually = True)
        runtime = prettyTimeDelta(runtimehours * 60 * 60, roundeventually = True)
        climbtime = prettyTimeDelta(climbtimehours * 60 * 60, roundeventually = True)
        crawltime = prettyTimeDelta(crawltimehours * 60 * 60, roundeventually = True)
        swimtime = prettyTimeDelta(swimtimehours * 60 * 60, roundeventually = True)

        defaultwalktime = prettyTimeDelta(defaultwalktimehours * 60 * 60, roundeventually = True)
        defaultruntime = prettyTimeDelta(defaultruntimehours * 60 * 60, roundeventually = True)
        defaultclimbtime = prettyTimeDelta(defaultclimbtimehours * 60 * 60, roundeventually = True)
        defaultcrawltime = prettyTimeDelta(defaultcrawltimehours * 60 * 60, roundeventually = True)
        defaultswimtime = prettyTimeDelta(defaultswimtimehours * 60 * 60, roundeventually = True)

        desc = (
            f"To {userstats.nickname}, {length:,.3mu} would look to be **{newlength:,.3mu}.** "
            f"They could walk that distance in **{walktime}** *({walksteps:,.0f} steps)*, "
            f"run that distance in **{runtime}** *({runsteps:,.0f} strides)*, "
            f"climb that distance in **{climbtime}** *({climbsteps:,.0f} pulls)*, "
            f"crawl that distance in **{crawltime}** *({crawlsteps:,.0f} pulls)*, "
            f"or swim that distance in **{swimtime}** *({swimsteps:,.0f} strokes.)*"
        )
        footer = (
            f"An average person could walk {length:,.3mu} in {defaultwalktime} ({defaultwalksteps:,.0f} steps), "
            f"run that distance in {defaultruntime} ({defaultrunsteps:,.0f} strides), "
            f"climb that distance in {defaultclimbtime} ({defaultclimbsteps:,.0f} pulls), ."
            f"crawl that distance in {defaultcrawltime} ({defaultcrawlsteps:,.0f} pulls), ."
            f"or swim that distance in {defaultswimtime} ({defaultswimsteps:,.0f} strokes.)"
        )

        if userdata.incomprehensible:
            desc = glitch_string(desc)
            footer = glitch_string(footer)

        e = discord.Embed(
            title = f"{length:,.3mu} to {userstats.nickname}",
            description = desc
        )
        e.set_footer(text = footer)

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
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2).save()

        userdata1 = getUserdata(memberOrHeight)
        userdata2 = getUserdata(memberOrHeight2)

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)
        embedtosend = await comparison.toEmbed(ctx.author.id)

        if userdata1.incomprehensible or userdata2.incomprehensible:
            ed = embedtosend.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string(field["value"])
            embedtosend = discord.Embed.from_dict(ed)
            embedtosend.set_footer(text = glitch_string(embedtosend.footer.text))

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
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2).save()

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
        aliases = ["reversedistance", "reversedist", "revdist"],
        usage = "<length> [user]",
        category = "stats"
    )
    async def ruler(self, ctx, length: SV, *, who: typing.Union[discord.Member, SV] = None):
        """A distance to a user looks how long to everyone else?

        Examples:
        `&ruler 1mi`
        `&ruler 1ft @DigiDuncan`"""

        if who is None:
            who = ctx.message.author

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} doesn't exist...")
            return

        newlength = SV(length / userstats.viewscale)

        desc = f"To everyone else, {userstats.nickname}'s {length:,.3mu} would look to be **{newlength:,.3mu}.**"
        if userdata.incomprehensible:
            desc = glitch_string(desc)

        e = discord.Embed(
            title = f"{userstats.nickname}'s {length:,.3mu} to the world",
            description = desc
        )

        await ctx.send(embed = e)

    @release_on("3.6")
    @commands.command(
        usage = "<user or length>",
        category = "stats"
    )
    async def sound(self, ctx, *, who: typing.Union[discord.Member, SV] = None):
        """Find how long it would take sound to travel a length or height."""
        ONE_SOUNDSECOND = SV(340.27)
        is_SV = False

        if who is None:
            who = ctx.message.author

        if isinstance(who, SV):
            is_SV = True

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        traveldist = userstats.height

        soundtime = TV(traveldist / ONE_SOUNDSECOND)
        printtime = prettyTimeDelta(soundtime, True, True)

        if is_SV:
            desc = f"To travel {traveldist:,.3mu}, it would take sound **{printtime}**."
        else:
            desc = f"To travel from **{userstats.nickname}**'s head to their {engine.plural(userstats.footname).lower()}, it would take sound **{printtime}**."

        embedtosend = discord.Embed(title = f"Sound Travel Time in {traveldist:,.3mu}",
                                    description = desc)

        await ctx.send(embed = embedtosend)

    @release_on("3.6")
    @commands.command(
        usage = "<user or length>",
        category = "stats"
    )
    async def light(self, ctx, *, who: typing.Union[discord.Member, SV] = None):
        """Find how long it would take light to travel a length or height."""
        ONE_LIGHTSECOND = SV(299792000)
        is_SV = False

        if who is None:
            who = ctx.message.author

        if isinstance(who, SV):
            is_SV = True

        userdata = getUserdata(who)
        userstats = proportions.PersonStats(userdata)

        traveldist = userstats.height

        lighttime = TV(traveldist / ONE_LIGHTSECOND)
        printtime = prettyTimeDelta(lighttime, True, True)

        if is_SV:
            desc = f"To travel {traveldist:,.3mu}, it would take light **{printtime}**."
        else:
            desc = f"To travel from **{userstats.nickname}**'s head to their {engine.plural(userstats.footname).lower()}, it would take light **{printtime}**."

        embedtosend = discord.Embed(title = f"Light Travel Time in {traveldist:,.3mu}",
                                    description = desc)

        await ctx.send(embed = embedtosend)

    @release_on("3.6")
    @commands.command(
        usage = "<distance>"
    )
    async def fall(self, ctx, distance: typing.Union[discord.Member, SV]):
        if isinstance(distance, discord.Member):
            ud = userdb.load(ctx.guild.id, distance.id)
            distance = ud.height
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        basemass = userdata.baseweight
        scale = userdata.scale
        time, _, _ = freefall(basemass, distance, scale)
        ftime = prettyTimeDelta(time, millisecondAccuracy = True, roundeventually = True)

        await ctx.send(f"You fell **{distance:,.3mu}** in {ftime}!")

    @commands.command(
        aliases = [],
        usage = "<users...>",
        category = "stats"
    )
    @commands.guild_only()
    async def lineup(self, ctx):
        """Lineup a bunch of people for comparison."""
        if not ctx.message.mentions:
            await ctx.send("At least one person is required")
            return

        failedusers = []
        userdatas = []
        for member in ctx.message.mentions:
            try:
                userdatas.append(userdb.load(member.guild.id, member.id, member=member))
            except errors.UserNotFoundException:
                failedusers.append(member)

        # TODO: Raise exception instead
        # Later Digi asks: why? This is fine?
        if failedusers:
            nicks = sentence_join((u.display_name for u in failedusers), oxford=True)
            if len(failedusers) == 1:
                failmessage = f"{nicks} is not a SizeBot user."
            else:
                failmessage = f"{nicks} are not SizeBot users."
            await ctx.send(failmessage)
            return

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        users = [{"name": u.nickname, "model": u.macrovision_model, "view": u.macrovision_view, "height": u.height} for u in userdatas]

        nicks = sentence_join((u.nickname for u in userdatas), oxford=True)
        e = discord.Embed(
            title="Click here for lineup image!",
            description=f"Lineup of {nicks}",
            color=colors.cyan,
            url = await macrovision.get_url(users)
        )
        await msg.edit(content = "", embed = e)


def getUserdata(memberOrSV, nickname = None, *, allow_unreg=False):
    if isinstance(memberOrSV, discord.Member):
        userdata = userdb.load(memberOrSV.guild.id, memberOrSV.id, member=memberOrSV, allow_unreg=allow_unreg)
    else:
        userdata = userdb.User()
        userdata.height = memberOrSV
        if nickname is None:
            nickname = f"a {userdata.height:,.3mu} tall person"
        userdata.nickname = nickname
    return userdata


def setup(bot):
    bot.add_cog(StatsCog(bot))
